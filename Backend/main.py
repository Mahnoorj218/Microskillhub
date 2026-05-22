import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import schemas as models
from ai_service import get_ai_career_advice
from auth_supabase import resolve_current_user, sign_in_user, sign_up_user
from db import delete_rows, fetch_all, fetch_one, insert_row, rpc, update_rows
from supabase_client import get_supabase, jwt_key_role, validate_service_role_key

load_dotenv()

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "Frontend"

app = FastAPI(title="Micro-Skill Hub API (Supabase)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROFICIENCY_MAP = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}


@app.get("/api/health")
async def health_check():
    key_role = None
    key_ok = True
    admin_api_ok = None
    try:
        validate_service_role_key()
        key_role = jwt_key_role(os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""))
        try:
            get_supabase().auth.admin.list_users(page=1, per_page=1)
            admin_api_ok = True
        except Exception as exc:
            admin_api_ok = False
            key_ok = False
            key_role = f"{key_role} (admin API: {exc})"
    except Exception as exc:
        key_ok = False
        key_role = str(exc)
    return {
        "status": "ok" if key_ok and admin_api_ok else "misconfigured",
        "frontend": FRONTEND_DIR.is_dir(),
        "supabase_key_role": key_role,
        "admin_api_ok": admin_api_ok,
        "hint": (
            None
            if key_ok and admin_api_ok
            else "Set SUPABASE_SERVICE_ROLE_KEY to service_role secret from Supabase → Settings → API (not anon)."
        ),
    }


async def get_current_user(authorization: str = Header(...)) -> dict:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token. Sign out and login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty token. Please sign out and login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return resolve_current_user(token)


@app.get("/api/auth/me")
async def auth_me(current_user: dict = Depends(get_current_user)):
    return current_user


def _attach_required_skills(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    client = get_supabase()
    for task in tasks:
        req = (
            client.table("task_required_skills")
            .select("skill_id, required_level, skills(skill_name)")
            .eq("task_id", task["task_id"])
            .execute()
        )
        task["required_skills"] = [
            {
                "skill_id": row["skill_id"],
                "skill_name": row["skills"]["skill_name"],
                "required_level": row["required_level"],
            }
            for row in (req.data or [])
            if row.get("skills")
        ]
    return tasks


# ==========================================
# AUTH ROUTES (Supabase Auth)
# ==========================================

@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
async def register(payload: models.RegisterRequest):
    return sign_up_user(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=payload.role,
        roll_number=payload.roll_number,
    )


@app.post("/api/auth/login", response_model=models.TokenResponse)
async def login(payload: models.LoginRequest):
    return sign_in_user(payload.email, payload.password, payload.role)


# ==========================================
# SKILLS ROUTES
# ==========================================

@app.get("/api/skills/all")
async def get_all_skills():
    return fetch_all("skills", "skill_id, skill_name, category")


@app.get("/api/skills/my-skills")
async def get_my_skills(current_user: dict = Depends(get_current_user)):
    client = get_supabase()
    response = (
        client.table("user_skills")
        .select(
            "user_skill_id, skill_id, proficiency_level, proficiency_percent, skills(skill_name)"
        )
        .eq("user_id", current_user["user_id"])
        .execute()
    )
    rows = []
    for row in response.data or []:
        rows.append(
            {
                "user_skill_id": row["user_skill_id"],
                "skill_id": row["skill_id"],
                "skill_name": row["skills"]["skill_name"],
                "proficiency_level": row["proficiency_level"],
                "proficiency_percent": row["proficiency_percent"],
            }
        )
    return rows


@app.post("/api/skills/add")
async def add_skill(
    payload: models.AddSkillRequest, current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can possess skills.")

    existing = fetch_one(
        "user_skills",
        "user_skill_id",
        user_id=current_user["user_id"],
        skill_id=payload.skill_id,
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="You have already logged this skill profile."
        )

    insert_row(
        "user_skills",
        {
            "user_id": current_user["user_id"],
            "skill_id": payload.skill_id,
            "proficiency_level": payload.proficiency_level,
            "proficiency_percent": payload.proficiency_percent,
        },
    )
    return {"success": True, "message": "Skill added successfully"}


@app.post("/api/skills/delete")
async def delete_skill(
    payload: models.DeleteSkillRequest, current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "student":
        raise HTTPException(
            status_code=403, detail="Action prohibited for this authorization level."
        )

    existing = fetch_one(
        "user_skills",
        "user_skill_id",
        user_skill_id=payload.user_skill_id,
        user_id=current_user["user_id"],
    )
    if not existing:
        raise HTTPException(
            status_code=404, detail="Skill mapping reference not found for this user."
        )

    delete_rows("user_skills", user_skill_id=payload.user_skill_id)
    return {"success": True, "message": "Skill removed successfully"}


# ==========================================
# TASKS ROUTES
# ==========================================

@app.get("/api/tasks/all")
async def get_all_tasks(current_user: dict = Depends(get_current_user)):
    tasks = fetch_all("tasks", "*", status="active")
    return _attach_required_skills(tasks)


@app.get("/api/tasks/my-applications")
async def get_my_applications(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students possess job metrics.")

    client = get_supabase()
    response = (
        client.table("applications")
        .select(
            "app_id, status, submission_text, applied_at, "
            "tasks(title, description, difficulty, reward_xp)"
        )
        .eq("user_id", current_user["user_id"])
        .execute()
    )

    results = []
    for row in response.data or []:
        task = row.get("tasks") or {}
        results.append(
            {
                "app_id": row["app_id"],
                "status": row["status"],
                "submission_text": row["submission_text"],
                "applied_at": row["applied_at"],
                "title": task.get("title"),
                "description": task.get("description"),
                "difficulty": task.get("difficulty"),
                "reward_xp": task.get("reward_xp"),
            }
        )
    return results


@app.post("/api/tasks/apply")
async def apply_to_task(
    payload: models.ApplyTaskRequest, current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can apply to active tasks.")

    existing = fetch_one(
        "applications",
        "app_id",
        user_id=current_user["user_id"],
        task_id=payload.task_id,
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="You have already registered an application for this task.",
        )

    insert_row(
        "applications",
        {
            "user_id": current_user["user_id"],
            "task_id": payload.task_id,
            "status": "pending",
        },
    )
    return {"success": True, "message": "Application lodged successfully"}


@app.post("/api/tasks/submit")
async def submit_proof(
    payload: models.SubmitProofRequest, current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "student":
        raise HTTPException(
            status_code=403, detail="Only students can submit task performance proof."
        )

    existing = fetch_one(
        "applications",
        "app_id",
        app_id=payload.app_id,
        user_id=current_user["user_id"],
    )
    if not existing:
        raise HTTPException(
            status_code=404,
            detail="Target tracking application reference was not found.",
        )

    update_rows(
        "applications",
        {"submission_text": payload.submission_text, "status": "pending"},
        app_id=payload.app_id,
    )
    return {
        "success": True,
        "message": "Proof of submission successfully dispatched for review.",
    }


# ==========================================
# MATCHING ROUTE
# ==========================================

@app.get("/api/match/recommend")
async def recommend_tasks(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "student":
        raise HTTPException(
            status_code=403,
            detail="Recommendations are curated strictly for student profiles.",
        )

    student_skills_rows = fetch_all(
        "user_skills",
        "skill_id, proficiency_level",
        user_id=current_user["user_id"],
    )
    student_skills = {
        row["skill_id"]: PROFICIENCY_MAP.get(row["proficiency_level"], 0)
        for row in student_skills_rows
    }

    tasks = fetch_all("tasks", "*", status="active")
    recommended_tasks = []

    for task in tasks:
        req_skills = fetch_all(
            "task_required_skills",
            "skill_id, required_level",
            task_id=task["task_id"],
        )
        if not req_skills:
            continue

        matched_count = 0
        for req in req_skills:
            req_level = PROFICIENCY_MAP.get(req["required_level"], 0)
            if student_skills.get(req["skill_id"], 0) >= req_level:
                matched_count += 1

        task["match_percent"] = round((matched_count / len(req_skills)) * 100, 2)
        recommended_tasks.append(task)

    recommended_tasks = _attach_required_skills(recommended_tasks)
    recommended_tasks.sort(key=lambda item: item["match_percent"], reverse=True)
    return recommended_tasks[:5]


# ==========================================
# LEADERBOARD
# ==========================================

@app.get("/api/leaderboard/global")
async def get_global_leaderboard(current_user: dict = Depends(get_current_user)):
    ranking = rpc("get_global_leaderboard")
    return {"ranking": ranking}


# ==========================================
# AI CHAT
# ==========================================

@app.post("/api/ai/chat", response_model=models.ChatResponse)
async def ai_chat(
    payload: models.ChatRequest, current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "student":
        raise HTTPException(
            status_code=403, detail="AI Assistant is dedicated to guiding student pathways."
        )

    client = get_supabase()
    response = (
        client.table("user_skills")
        .select(
            "proficiency_level, proficiency_percent, skills(skill_name)"
        )
        .eq("user_id", current_user["user_id"])
        .execute()
    )
    skills_list = [
        {
            "skill_name": row["skills"]["skill_name"],
            "proficiency_level": row["proficiency_level"],
            "proficiency_percent": row["proficiency_percent"],
        }
        for row in (response.data or [])
        if row.get("skills")
    ]

    advice = await get_ai_career_advice(payload.message, skills_list)
    return {"reply": advice}


# ==========================================
# ADMIN ROUTES
# ==========================================

@app.get("/api/admin/stats")
async def get_admin_stats(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization privileges required.")

    students = len(fetch_all("profiles", "id", role="student"))
    tasks = len(fetch_all("tasks", "task_id"))
    pending = len(fetch_all("applications", "app_id", status="pending"))
    completions = len(fetch_all("applications", "app_id", status="completed"))

    return {
        "students": students,
        "tasks": tasks,
        "pending": pending,
        "completions": completions,
    }


@app.get("/api/admin/submissions")
async def get_pending_submissions(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin clearance credentials missing.")

    client = get_supabase()
    response = (
        client.table("applications")
        .select(
            "app_id, submission_text, status, applied_at, "
            "profiles(full_name, email), tasks(title, reward_xp)"
        )
        .eq("status", "pending")
        .execute()
    )

    rows = []
    for item in response.data or []:
        profile = item.get("profiles") or {}
        task = item.get("tasks") or {}
        rows.append(
            {
                "app_id": item["app_id"],
                "submission_text": item["submission_text"],
                "status": item["status"],
                "applied_at": item["applied_at"],
                "student_name": profile.get("full_name"),
                "student_email": profile.get("email"),
                "task_title": task.get("title"),
                "reward_xp": task.get("reward_xp"),
            }
        )
    return rows


@app.post("/api/admin/review")
async def review_submission(
    payload: models.ReviewRequest, current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=403, detail="Administrative access clearance mapping rejection."
        )

    application = fetch_one(
        "applications", "user_id, task_id, status", app_id=payload.app_id
    )
    if not application:
        raise HTTPException(
            status_code=404,
            detail="Target tracking submission application index records invalid.",
        )

    new_status = "completed" if payload.action == "approve" else "rejected"
    update_rows("applications", {"status": new_status}, app_id=payload.app_id)

    if payload.action == "approve":
        task_info = fetch_one("tasks", "reward_xp", task_id=application["task_id"])
        if task_info:
            insert_row(
                "experience",
                {
                    "user_id": application["user_id"],
                    "app_id": payload.app_id,
                    "xp_earned": task_info["reward_xp"],
                },
            )

    return {
        "success": True,
        "message": f"Submission status transitioned to '{new_status}' completely.",
    }


@app.post("/api/admin/create-task")
async def create_task(
    payload: models.CreateTaskRequest, current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=403, detail="Administrative elevation authorization required."
        )

    task = insert_row(
        "tasks",
        {
            "title": payload.title,
            "description": payload.description,
            "difficulty": payload.difficulty,
            "reward_xp": payload.reward_xp,
            "status": "active",
            "created_by": current_user["user_id"],
        },
    )
    task_id = task["task_id"]

    for skill_id in payload.required_skills:
        insert_row(
            "task_required_skills",
            {
                "task_id": task_id,
                "skill_id": skill_id,
                "required_level": "Intermediate",
            },
        )

    return {
        "success": True,
        "message": "Task and context dependencies logged successfully.",
        "task_id": task_id,
    }


@app.post("/api/admin/delete-task/{task_id}")
async def delete_task(task_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required.")

    pending = fetch_one("applications", "app_id", task_id=task_id, status="pending")
    if pending:
        raise HTTPException(
            status_code=400,
            detail="Cannot purge a task holding pending un-reviewed user submissions.",
        )

    delete_rows("task_required_skills", task_id=task_id)
    delete_rows("applications", task_id=task_id)
    delete_rows("tasks", task_id=task_id)

    return {"success": True, "message": "Task structure purged successfully from data tables."}


@app.get("/api/admin/users")
async def get_all_users_reporting(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required.")

    students = fetch_all(
        "profiles", "id, full_name, email, roll_number", role="student"
    )
    results = []

    for student in students:
        skill_count = len(
            fetch_all("user_skills", "user_skill_id", user_id=student["id"])
        )
        xp_rows = fetch_all("experience", "xp_earned", user_id=student["id"])
        total_xp = sum(row.get("xp_earned", 0) for row in xp_rows)
        results.append(
            {
                "user_id": student["id"],
                "full_name": student["full_name"],
                "email": student["email"],
                "roll_number": student["roll_number"],
                "skill_count": skill_count,
                "total_xp": total_xp,
            }
        )

    return results


@app.post("/api/admin/create-student", status_code=status.HTTP_201_CREATED)
async def admin_create_student(
    payload: models.AdminCreateStudentRequest,
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required.")

    if fetch_one("profiles", "id", email=payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    client = get_supabase()
    try:
        auth_res = client.auth.admin.create_user(
            {
                "email": payload.email,
                "password": payload.password,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": payload.full_name,
                    "role": "student",
                    "roll_number": payload.roll_number,
                },
            }
        )
    except Exception as exc:
        msg = str(exc)
        configured_role = jwt_key_role(os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""))
        if "not allowed" in msg.lower() or "unauthorized" in msg.lower():
            raise HTTPException(
                status_code=403,
                detail=(
                    "Supabase admin API blocked. "
                    f"Configured key role: {configured_role or 'unknown'}. "
                    "Supabase Dashboard → Project Settings → API → copy **service_role** (secret), "
                    "not anon/public. Local: Backend/.env + server restart. "
                    "Railway: Variables tab → SUPABASE_SERVICE_ROLE_KEY → Redeploy. "
                    f"Check /api/health on this server. ({msg})"
                ),
            ) from exc
        if "already been registered" in msg.lower() or "already exists" in msg.lower():
            raise HTTPException(status_code=400, detail="Email already registered") from exc
        raise HTTPException(status_code=400, detail=msg) from exc

    if not auth_res.user:
        raise HTTPException(status_code=400, detail="Failed to create student account")

    try:
        insert_row(
            "profiles",
            {
                "id": auth_res.user.id,
                "full_name": payload.full_name,
                "email": payload.email,
                "role": "student",
                "roll_number": payload.roll_number,
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Auth user created but profile insert failed: {exc}",
        ) from exc

    return {"success": True, "message": "Student account created", "user_id": auth_res.user.id}


@app.put("/api/admin/update-task/{task_id}")
async def admin_update_task(
    task_id: int,
    payload: models.UpdateTaskRequest,
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required.")

    if not fetch_one("tasks", "task_id", task_id=task_id):
        raise HTTPException(status_code=404, detail="Task not found")

    update_rows(
        "tasks",
        {
            "title": payload.title,
            "description": payload.description,
            "difficulty": payload.difficulty,
            "reward_xp": payload.reward_xp,
            "status": payload.status,
        },
        task_id=task_id,
    )

    delete_rows("task_required_skills", task_id=task_id)
    for skill_id in payload.required_skills:
        insert_row(
            "task_required_skills",
            {
                "task_id": task_id,
                "skill_id": skill_id,
                "required_level": "Intermediate",
            },
        )

    return {"success": True, "message": "Task updated successfully", "task_id": task_id}


@app.get("/api/admin/all-applications")
async def admin_all_applications(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required.")

    client = get_supabase()
    response = (
        client.table("applications")
        .select(
            "app_id, status, submission_text, applied_at, reviewed_at, "
            "profiles(full_name, email), tasks(title, difficulty, reward_xp)"
        )
        .order("applied_at", desc=True)
        .execute()
    )

    rows = []
    for item in response.data or []:
        profile = item.get("profiles") or {}
        task = item.get("tasks") or {}
        rows.append(
            {
                "app_id": item["app_id"],
                "status": item["status"],
                "submission_text": item["submission_text"],
                "applied_at": item["applied_at"],
                "student_name": profile.get("full_name"),
                "student_email": profile.get("email"),
                "task_title": task.get("title"),
                "task_difficulty": task.get("difficulty"),
                "reward_xp": task.get("reward_xp"),
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Frontend (single-server): API routes above; static files last
# ---------------------------------------------------------------------------
if FRONTEND_DIR.is_dir():
    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="frontend",
    )
else:
    import warnings

    warnings.warn(f"Frontend folder not found: {FRONTEND_DIR}", stacklevel=1)
