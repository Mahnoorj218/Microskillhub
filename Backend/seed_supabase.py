"""
Seed Supabase with admin user + sample tasks.
Run after applying supabase/migrations/001_initial.sql

  cd Backend
  .\\venv\\Scripts\\python.exe seed_supabase.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

from supabase_client import get_supabase
from db import fetch_one, insert_row


ADMIN_EMAIL = os.getenv("SEED_ADMIN_EMAIL", "admin@microskillhub.com")
ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "admin123")
ADMIN_NAME = "System Administrator"
ADMIN_ROLL = "ADMIN-001"


def ensure_admin():
    client = get_supabase()

    existing = fetch_one("profiles", "id", email=ADMIN_EMAIL)
    if existing:
        print(f"Admin profile already exists: {ADMIN_EMAIL}")
        return existing["id"]

    print(f"Creating admin user: {ADMIN_EMAIL}")
    auth_res = client.auth.admin.create_user(
        {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "email_confirm": True,
            "user_metadata": {
                "full_name": ADMIN_NAME,
                "role": "admin",
                "roll_number": ADMIN_ROLL,
            },
        }
    )

    user_id = auth_res.user.id
    insert_row(
        "profiles",
        {
            "id": user_id,
            "full_name": ADMIN_NAME,
            "email": ADMIN_EMAIL,
            "role": "admin",
            "roll_number": ADMIN_ROLL,
        },
    )
    print("Admin created successfully.")
    return user_id


def ensure_sample_tasks(admin_id: str):
    from db import fetch_all

    if fetch_all("tasks", "task_id"):
        print("Tasks already exist — skipping sample tasks.")
        return

    task1 = insert_row(
        "tasks",
        {
            "title": "Build a Responsive Navbar",
            "description": "Create a responsive navigation header using Flexbox/Grid.",
            "difficulty": "Intermediate",
            "reward_xp": 150,
            "status": "active",
            "created_by": admin_id,
        },
    )
    task2 = insert_row(
        "tasks",
        {
            "title": "User Registration Backend Script",
            "description": "Write a secure registration API with validation and hashed passwords.",
            "difficulty": "Advanced",
            "reward_xp": 300,
            "status": "active",
            "created_by": admin_id,
        },
    )

    reqs = [
        (task1["task_id"], 1, "Intermediate"),
        (task1["task_id"], 2, "Intermediate"),
        (task2["task_id"], 4, "Advanced"),
        (task2["task_id"], 5, "Intermediate"),
    ]
    for task_id, skill_id, level in reqs:
        insert_row(
            "task_required_skills",
            {"task_id": task_id, "skill_id": skill_id, "required_level": level},
        )

    print("Sample tasks seeded.")


def main():
    try:
        admin_id = ensure_admin()
        ensure_sample_tasks(admin_id)
        print("\nDone. Login with:")
        print(f"  Email:    {ADMIN_EMAIL}")
        print(f"  Password: {ADMIN_PASSWORD}")
        print("  Role:     admin")
    except Exception as exc:
        print(f"Seed failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
