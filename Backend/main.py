import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
import mysql.connector

# Import database utilities, Pydantic models, and AI chat function
from db import get_db_cursor, close_db, get_db_connection
import schemas as models
from ai_service import get_ai_career_advice

# Load system configurations
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "microskillhub_super_secret_key_2026")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# Initialize password hashing engine
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="Micro-Skill Hub API")

# Configure Development CORS Policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper Hashing Functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ==========================================
# DEPENDENCY: get_current_user
# ==========================================
async def get_current_user(authorization: str = Header(...)) -> dict:
    """
    Decodes the Bearer token from the Authorization header and verifies the user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        if not authorization.startswith("Bearer "):
            raise credentials_exception
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        name: str = payload.get("name")
        
        if user_id is None or role is None:
            raise credentials_exception
            
        return {"user_id": user_id, "role": role, "name": name}
    except JWTError:
        raise credentials_exception


# ==========================================
# AUTH ROUTES
# ==========================================

@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
async def register(payload: models.RegisterRequest):
    conn, cursor = get_db_cursor()
    try:
        # Check if email exists (Changed 'id' to 'user_id' to match schema)
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (payload.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_pwd = hash_password(payload.password)
        
        # Changed 'password' to 'password_hash' to match schema
        query = """
            INSERT INTO users (full_name, email, password_hash, role, roll_number)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (payload.full_name, payload.email, hashed_pwd, payload.role, payload.roll_number))
        conn.commit()
        return {"success": True, "message": "Registered successfully"}
    except mysql.connector.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database transaction failure: {str(e)}")
    finally:
        close_db(conn, cursor)


@app.post("/api/auth/login", response_model=models.TokenResponse)
async def login(payload: models.LoginRequest):
    conn, cursor = get_db_cursor()
    try:
        # Changed 'id' to 'user_id' and 'password' to 'password_hash' to match schema
        cursor.execute("SELECT user_id, full_name, password_hash, role FROM users WHERE email = %s", (payload.email,))
        user = cursor.fetchone()
        
        if not user or not verify_password(payload.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid email or password")
            
        if user['role'] != payload.role:
            raise HTTPException(status_code=403, detail="Role mismatch for this user profile")
            
        token_data = {"user_id": user['user_id'], "role": user['role'], "name": user['full_name']}
        token = create_access_token(token_data)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "role": user['role'],
            "name": user['full_name'],
            "user_id": user['user_id']
        }
    finally:
        close_db(conn, cursor)


# ==========================================
# SKILLS ROUTES
# ==========================================

@app.get("/api/skills/all")
async def get_all_skills():
    conn, cursor = get_db_cursor()
    try:
        # Changed 'id' to 'skill_id' to match schema
        cursor.execute("SELECT skill_id, skill_name, category FROM skills")
        return cursor.fetchall()
    finally:
        close_db(conn, cursor)


@app.get("/api/skills/my-skills")
async def get_my_skills(current_user: dict = Depends(get_current_user)):
    conn, cursor = get_db_cursor()
    try:
        # Changed primary key names to match user_skills schema
        query = """
            SELECT us.user_skill_id, us.skill_id, s.skill_name, us.proficiency_level, us.proficiency_percent 
            FROM user_skills us
            JOIN skills s ON us.skill_id = s.skill_id
            WHERE us.user_id = %s
        """
        cursor.execute(query, (current_user['user_id'],))
        return cursor.fetchall()
    finally:
        close_db(conn, cursor)


@app.post("/api/skills/add")
async def add_skill(payload: models.AddSkillRequest, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != "student":
        raise HTTPException(status_code=403, detail="Only students can possess skills.")
        
    conn, cursor = get_db_cursor()
    try:
        # Changed 'id' to 'user_skill_id'
        cursor.execute(
            "SELECT user_skill_id FROM user_skills WHERE user_id = %s AND skill_id = %s",
            (current_user['user_id'], payload.skill_id)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="You have already logged this skill profile.")

        query = """
            INSERT INTO user_skills (user_id, skill_id, proficiency_level, proficiency_percent)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (current_user['user_id'], payload.skill_id, payload.proficiency_level, payload.proficiency_percent))
        conn.commit()
        return {"success": True, "message": "Skill added successfully"}
    except mysql.connector.Error:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to add skill details.")
    finally:
        close_db(conn, cursor)


@app.post("/api/skills/delete")
async def delete_skill(payload: models.DeleteSkillRequest, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != "student":
        raise HTTPException(status_code=403, detail="Action prohibited for this authorization level.")
        
    conn, cursor = get_db_cursor()
    try:
        # Changed 'id' to 'user_skill_id'
        cursor.execute(
            "SELECT user_skill_id FROM user_skills WHERE user_skill_id = %s AND user_id = %s",
            (payload.user_skill_id, current_user['user_id'])
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Skill mapping reference not found for this user.")

        cursor.execute("DELETE FROM user_skills WHERE user_skill_id = %s", (payload.user_skill_id,))
        conn.commit()
        return {"success": True, "message": "Skill removed successfully"}
    except mysql.connector.Error:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to remove target skill record.")
    finally:
        close_db(conn, cursor)


# ==========================================
# TASKS ROUTES
# ==========================================

@app.get("/api/tasks/all")
async def get_all_tasks(current_user: dict = Depends(get_current_user)):
    conn, cursor = get_db_cursor()
    try:
        # Changed 'is_active = TRUE' to status = 'active' to match schema
        cursor.execute("SELECT * FROM tasks WHERE status = 'active'")
        tasks = cursor.fetchall()
        
        for task in tasks:
            # Updated cross-reference table mapping names to task_required_skills
            query = """
                SELECT s.skill_name, ts.required_level FROM task_required_skills ts
                JOIN skills s ON ts.skill_id = s.skill_id
                WHERE ts.task_id = %s
            """
            cursor.execute(query, (task['task_id'],))
            task['required_skills'] = cursor.fetchall()
            
        return tasks
    finally:
        close_db(conn, cursor)


@app.get("/api/tasks/my-applications")
async def get_my_applications(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != "student":
        raise HTTPException(status_code=403, detail="Only students possess job metrics.")
        
    conn, cursor = get_db_cursor()
    try:
        # Fixed 'a.id' and 't.id' targets
        query = """
            SELECT a.app_id, a.status, a.submission_text, a.applied_at,
                   t.title, t.description, t.difficulty, t.reward_xp
            FROM applications a
            JOIN tasks t ON a.task_id = t.task_id
            WHERE a.user_id = %s
        """
        cursor.execute(query, (current_user['user_id'],))
        return cursor.fetchall()
    finally:
        close_db(conn, cursor)


@app.post("/api/tasks/apply")
async def apply_to_task(payload: models.ApplyTaskRequest, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != "student":
        raise HTTPException(status_code=403, detail="Only students can apply to active tasks.")
        
    conn, cursor = get_db_cursor()
    try:
        # Fixed 'id' to 'app_id'
        cursor.execute(
            "SELECT app_id FROM applications WHERE user_id = %s AND task_id = %s",
            (current_user['user_id'], payload.task_id)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="You have already registered an application for this task.")

        query = "INSERT INTO applications (user_id, task_id, status) VALUES (%s, %s, 'pending')"
        cursor.execute(query, (current_user['user_id'], payload.task_id))
        conn.commit()
        return {"success": True, "message": "Application lodged successfully"}
    except mysql.connector.Error:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed to process your task application.")
    finally:
        close_db(conn, cursor)


@app.post("/api/tasks/submit-proof")
async def submit_proof(payload: models.SubmitProofRequest, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != "student":
        raise HTTPException(status_code=403, detail="Only students can submit task performance proof.")
        
    conn, cursor = get_db_cursor()
    try:
        # Fixed 'id' to 'app_id'
        cursor.execute(
            "SELECT app_id FROM applications WHERE app_id = %s AND user_id = %s",
            (payload.app_id, current_user['user_id'])
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Target tracking application reference was not found.")

        query = "UPDATE applications SET submission_text = %s, status = 'pending' WHERE app_id = %s"
        cursor.execute(query, (payload.submission_text, payload.app_id))
        conn.commit()
        return {"success": True, "message": "Proof of submission successfully dispatched for review."}
    except mysql.connector.Error:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Failed saving tracking details.")
    finally:
        close_db(conn, cursor)


# ==========================================
# MATCHING ROUTE
# ==========================================

@app.get("/api/match/recommend")
async def recommend_tasks(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != "student":
        raise HTTPException(status_code=403, detail="Recommendations are curated strictly for student profiles.")
        
    conn, cursor = get_db_cursor()
    try:
        prof_map = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}
        
        cursor.execute("SELECT skill_id, proficiency_level FROM user_skills WHERE user_id = %s", (current_user['user_id'],))
        student_skills = {row['skill_id']: prof_map.get(row['proficiency_level'], 0) for row in cursor.fetchall()}
        
        # Fixed status match query filter
        cursor.execute("SELECT * FROM tasks WHERE status = 'active'")
        tasks = cursor.fetchall()
        
        recommended_tasks = []
        
        for task in tasks:
            # Fixed table relationships to match schema names
            cursor.execute("SELECT skill_id, required_level FROM task_required_skills WHERE task_id = %s", (task['task_id'],))
            req_skills = cursor.fetchall()
            
            if not req_skills:
                continue
                
            matched_count = 0
            for r_skill in req_skills:
                s_id = r_skill['skill_id']
                req_level_num = prof_map.get(r_skill['required_level'], 0)
                
                if s_id in student_skills and student_skills[s_id] >= req_level_num:
                    matched_count += 1
            
            match_percent = (matched_count / len(req_skills)) * 100 if req_skills else 0
            task['match_percent'] = round(match_percent, 2)
            
            cursor.execute("""
                SELECT s.skill_name, ts.required_level FROM task_required_skills ts 
                JOIN skills s ON ts.skill_id = s.skill_id WHERE ts.task_id = %s
            """, (task['task_id'],))
            task['required_skills'] = cursor.fetchall()
            
            recommended_tasks.append(task)
            
        recommended_tasks.sort(key=lambda x: x['match_percent'], reverse=True)
        return recommended_tasks[:5]
    finally:
        close_db(conn, cursor)


# ==========================================
# AI CHAT ROUTE
# ==========================================

@app.post("/api/ai/chat", response_model=models.ChatResponse)
async def ai_chat(payload: models.ChatRequest, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != "student":
        raise HTTPException(status_code=403, detail="AI Assistant is dedicated to guiding student pathways.")
        
    conn, cursor = get_db_cursor()
    try:
        query = """
            SELECT s.skill_name, us.proficiency_level, us.proficiency_percent 
            FROM user_skills us
            JOIN skills s ON us.skill_id = s.skill_id
            WHERE us.user_id = %s
        """
        cursor.execute(query, (current_user['user_id'],))
        skills_list = cursor.fetchall()
    finally:
        close_db(conn, cursor)
        
    advice = await get_ai_career_advice(payload.message, skills_list)
    return {"reply": advice}


# ==========================================
# ADMIN ROUTES
# ==========================================

@app.get("/api/admin/stats")
async def get_admin_stats(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization privileges required.")
        
    conn, cursor = get_db_cursor()
    try:
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'student'")
        students = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM tasks")
        tasks = cursor.fetchone()['count']
        
        # Updated pending status target check to match default 'pending' enum template
        cursor.execute("SELECT COUNT(*) as count FROM applications WHERE status = 'pending'")
        pending = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM applications WHERE status = 'completed'")
        completions = cursor.fetchone()['count']
        
        return {
            "students": students,
            "tasks": tasks,
            "pending": pending,
            "completions": completions
        }
    finally:
        close_db(conn, cursor)


@app.get("/api/admin/submissions")
async def get_pending_submissions(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != "admin":
        raise HTTPException(status_code=403, detail="Admin clearance credentials missing.")
        
    conn, cursor = get_db_cursor()
    try:
        # Fixed explicit system column connections
        query = """
            SELECT a.app_id, a.submission_text, a.status, a.applied_at,
                   u.full_name as student_name, u.email as student_email,
                   t.title as task_title, t.reward_xp
            FROM applications a
            JOIN users u ON a.user_id = u.user_id
            JOIN tasks t ON a.task_id = t.task_id
            WHERE a.status = 'pending'
        """
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        close_db(conn, cursor)


@app.post("/api/admin/review")
async def review_submission(payload: models.ReviewRequest, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != "admin":
        raise HTTPException(status_code=403, detail="Administrative access clearance mapping rejection.")
        
    conn, cursor = get_db_cursor()
    try:
        # Changed 'id' to 'app_id'
        cursor.execute("SELECT user_id, task_id, status FROM applications WHERE app_id = %s", (payload.app_id,))
        application = cursor.fetchone()
        
        if not application:
            raise HTTPException(status_code=404, detail="Target tracking submission application index records invalid.")
            
        new_status = "completed" if payload.action == "approve" else "rejected"
        
        cursor.execute("UPDATE applications SET status = %s WHERE app_id = %s", (new_status, payload.app_id))
        
        if payload.action == "approve":
            cursor.execute("SELECT reward_xp FROM tasks WHERE task_id = %s", (application['task_id'],))
            task_info = cursor.fetchone()
            
            # Changed 'xp_gained' to 'xp_earned' to match script schema layout definitions
            xp_query = "INSERT INTO experience (user_id, app_id, xp_earned) VALUES (%s, %s, %s)"
            cursor.execute(xp_query, (application['user_id'], payload.app_id, task_info['reward_xp']))
            
        conn.commit()
        return {"success": True, "message": f"Submission status transitioned to '{new_status}' completely."}
    except mysql.connector.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database transaction operational breakdown: {str(e)}")
    finally:
        close_db(conn, cursor)


@app.post("/api/admin/create-task")
async def create_task(payload: models.CreateTaskRequest, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != "admin":
        raise HTTPException(status_code=403, detail="Administrative elevation authorization required.")
        
    conn, cursor = get_db_cursor()
    try:
        # Fixed 'is_active' mapping pattern variables to default 'active' strings definitions
        task_query = """
            INSERT INTO tasks (title, description, difficulty, reward_xp, status, created_by)
            VALUES (%s, %s, %s, %s, 'active', %s)
        """
        cursor.execute(task_query, (payload.title, payload.description, payload.difficulty, payload.reward_xp, current_user['user_id']))
        task_id = cursor.lastrowid
        
        for s_id in payload.required_skills:
            cursor.execute(
                "INSERT INTO task_required_skills (task_id, skill_id, required_level) VALUES (%s, %s, 'Intermediate')",
                (task_id, s_id)
            )
            
        conn.commit()
        return {"success": True, "message": "Task and context dependencies logged successfully.", "task_id": task_id}
    except mysql.connector.Error:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Administrative operational pipeline database write error.")
    finally:
        close_db(conn, cursor)


@app.post("/api/admin/delete-task/{task_id}")
async def delete_task(task_id: int, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required.")
        
    conn, cursor = get_db_cursor()
    try:
        # Changed 'id' to 'app_id' and verification string filter checks to 'pending' strings layouts
        cursor.execute("SELECT app_id FROM applications WHERE task_id = %s AND status = 'pending'", (task_id,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Cannot purge a task holding pending un-reviewed user submissions.")
            
        cursor.execute("DELETE FROM task_required_skills WHERE task_id = %s", (task_id,))
        cursor.execute("DELETE FROM applications WHERE task_id = %s", (task_id,))
        cursor.execute("DELETE FROM tasks WHERE task_id = %s", (task_id,))
        
        conn.commit()
        return {"success": True, "message": "Task structure purged successfully from data tables."}
    except mysql.connector.Error:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Purge transaction operational sequence failure.")
    finally:
        close_db(conn, cursor)


@app.get("/api/admin/users")
async def get_all_users_reporting(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required.")
        
    conn, cursor = get_db_cursor()
    try:
        # Mapped primary key targets perfectly to user_id models layouts
        query = """
            SELECT u.user_id, u.full_name, u.email, u.roll_number,
                   (SELECT COUNT(*) FROM user_skills WHERE user_id = u.user_id) as skill_count,
                   IFNULL((SELECT SUM(xp_earned) FROM experience WHERE user_id = u.user_id), 0) as total_xp
            FROM users u
            WHERE u.role = 'student'
        """
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        close_db(conn, cursor)