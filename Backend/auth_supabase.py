"""Supabase Auth helpers for FastAPI."""

from typing import Any, Dict

from fastapi import HTTPException, status

from db import fetch_one, insert_row
from supabase_client import get_supabase


def sign_up_user(
    email: str,
    password: str,
    full_name: str,
    role: str,
    roll_number: str,
) -> Dict[str, Any]:
    client = get_supabase()

    existing = fetch_one("profiles", "id", email=email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # admin.create_user + email_confirm avoids signup confirmation emails
    # (sign_up hits Supabase "email rate limit exceeded" on free SMTP)
    try:
        auth_res = client.auth.admin.create_user(
            {
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": full_name,
                    "role": role,
                    "roll_number": roll_number,
                },
            }
        )
    except Exception as exc:
        msg = str(exc)
        if "rate limit" in msg.lower():
            raise HTTPException(
                status_code=429,
                detail=(
                    "Supabase email rate limit reached. Wait 1 hour or disable "
                    "Confirm email in Supabase → Authentication → Providers → Email."
                ),
            ) from exc
        raise HTTPException(status_code=400, detail=msg) from exc

    if not auth_res.user:
        raise HTTPException(status_code=400, detail="Registration failed")

    try:
        insert_row(
            "profiles",
            {
                "id": auth_res.user.id,
                "full_name": full_name,
                "email": email,
                "role": role,
                "roll_number": roll_number,
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Profile creation failed: {exc}",
        ) from exc

    return {"success": True, "message": "Registered successfully"}


def sign_in_user(email: str, password: str, role: str) -> Dict[str, Any]:
    client = get_supabase()

    try:
        auth_res = client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not auth_res.session or not auth_res.user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    profile = fetch_one(
        "profiles",
        "id, full_name, role",
        id=auth_res.user.id,
    )
    if not profile:
        raise HTTPException(status_code=401, detail="User profile not found")

    if profile["role"] != role:
        raise HTTPException(
            status_code=403,
            detail="Role mismatch for this user profile",
        )

    return {
        "access_token": auth_res.session.access_token,
        "token_type": "bearer",
        "role": profile["role"],
        "name": profile["full_name"],
        "user_id": profile["id"],
    }


def resolve_current_user(token: str) -> Dict[str, Any]:
    client = get_supabase()

    try:
        user_res = client.auth.get_user(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if not user_res or not user_res.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    profile = fetch_one(
        "profiles",
        "id, full_name, role",
        id=user_res.user.id,
    )
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "user_id": profile["id"],
        "role": profile["role"],
        "name": profile["full_name"],
    }
