import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"

# Fallback if primary model unavailable for the account
OPENAI_FALLBACK_MODELS = ("gpt-4o-mini", "gpt-3.5-turbo")


def _openai_error_message(status_code: int, body: str) -> str:
    try:
        err = json.loads(body).get("error", {})
        msg = err.get("message", body[:200])
        code = err.get("code", "") or err.get("type", "")
    except Exception:
        msg = body[:200] if body else "Unknown error"
        code = status_code

    lower = str(msg).lower()
    if status_code == 401 or "invalid_api_key" in lower or "incorrect api key" in lower:
        return (
            "Invalid OpenAI API key. Set OPENAI_API_KEY in Backend/.env or Railway Variables "
            "(https://platform.openai.com/api-keys)."
        )
    if status_code == 429 or "rate limit" in lower or "quota" in lower:
        return (
            "OpenAI quota or rate limit reached. Check billing at "
            "https://platform.openai.com/account/billing and try again."
        )
    if "model" in lower and ("not found" in lower or "does not exist" in lower):
        return f"OpenAI model not available: {msg}. Set OPENAI_MODEL=gpt-4o-mini in .env."
    return f"OpenAI API error ({code or status_code}): {msg}"


def check_openai_api() -> dict:
    """Lightweight health probe for /api/health."""
    if not OPENAI_API_KEY:
        return {
            "ok": False,
            "detail": "OPENAI_API_KEY is not set in environment variables.",
        }

    try:
        response = requests.post(
            OPENAI_CHAT_URL,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENAI_MODEL,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 5,
            },
            timeout=25,
        )
    except requests.RequestException as exc:
        return {"ok": False, "detail": f"Cannot reach OpenAI API: {exc}"}

    if response.status_code == 200:
        return {"ok": True, "model": OPENAI_MODEL}

    return {"ok": False, "detail": _openai_error_message(response.status_code, response.text)}


def _call_openai(system_prompt: str, user_prompt: str) -> tuple[str | None, str | None]:
    """Returns (reply_text, error_detail)."""
    if not OPENAI_API_KEY:
        return None, (
            "AI is not configured. Add OPENAI_API_KEY to Backend/.env or Railway Variables "
            "(https://platform.openai.com/api-keys), then restart the server."
        )

    models = []
    for m in (OPENAI_MODEL, *OPENAI_FALLBACK_MODELS):
        if m and m not in models:
            models.append(m)

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    last_error = None

    for model in models:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 350,
            "temperature": 0.7,
        }
        try:
            response = requests.post(
                OPENAI_CHAT_URL,
                headers=headers,
                json=payload,
                timeout=60,
            )
        except requests.RequestException as exc:
            last_error = f"Network error ({model}): {exc}"
            continue

        if response.status_code == 200:
            try:
                text = (
                    response.json()["choices"][0]["message"]["content"].strip()
                )
                return text, None
            except (KeyError, IndexError, TypeError) as exc:
                last_error = f"Unexpected OpenAI response ({model}): {exc}"
                continue

        last_error = _openai_error_message(response.status_code, response.text)
        if response.status_code in (401, 429):
            break
        if "model" not in (last_error or "").lower():
            break

    return None, last_error or "OpenAI request failed for all configured models."


async def get_ai_career_advice(user_message: str, user_skills: list) -> str:
    system_instruction = (
        "You are SkillCopilot, an AI career assistant for Micro-Skill Hub — a platform "
        "that helps university students build technical skills through tasks and tracking. "
        "Give friendly, practical guidance on careers, skill improvement, and task choices. "
        "Keep answers under 120 words and focus on one topic at a time."
    )

    skills_formatted = []
    for skill in user_skills:
        if isinstance(skill, dict):
            name = skill.get("skill_name", "Unknown Skill")
            level = skill.get("proficiency_level", "Unknown Level")
            percent = skill.get("proficiency_percent", 0)
            skills_formatted.append(f"{name} ({level} {percent}%)")
        else:
            skills_formatted.append(str(skill))

    skills_context = ", ".join(skills_formatted) if skills_formatted else "None listed yet"
    user_prompt = (
        f"Student skills: {skills_context}\n\n"
        f"Student question: {user_message}"
    )

    reply, error = _call_openai(system_instruction, user_prompt)
    if reply:
        return reply

    print(f"[AI ERROR] {error}")
    return error or "Sorry, AI assistant is temporarily unable to process the request."
