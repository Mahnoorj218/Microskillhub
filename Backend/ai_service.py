import os
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

async def get_ai_career_advice(user_message: str, user_skills: list) -> str:
    """
    Generates career advice ensuring 100% UTF-8 safe encoding for Urdu and special symbols (+, &, %).
    """
    try:
        system_instruction = (
            "You are an AI Career Assistant for Micro-Skill Hub, a platform that helps university students develop technical skills. "
            "You help students with career guidance, skill improvement tips, and task recommendations. "
            "Be friendly, concise, and give practical advice. Strictly keep responses under 120 words and focus on one topic at a time."
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
        full_prompt = f"{system_instruction}\n\nStudent skills: {skills_context}\n\nStudent Question: {user_message}"

        # Safe Headers Configuration
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
        params = {"key": GEMINI_API_KEY}

        # Model Execution Matrix
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
            # Explicitly forcing json data to encode as safe UTF-8 bytes
            response = requests.post(url, json=payload, headers=headers, params=params)
            if response.status_code == 200:
                # Ensure we read the response in UTF-8 safely
                response.encoding = 'utf-8'
                return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except Exception:
            pass

        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
            response = requests.post(url, json=payload, headers=headers, params=params)
            if response.status_code == 200:
                response.encoding = 'utf-8'
                return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except Exception:
            pass

        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"
        response = requests.post(url, json=payload, headers=headers, params=params)
        
        if response.status_code == 200:
            response.encoding = 'utf-8'
            return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            print(f"[HTTP AI ERROR] Status: {response.status_code}, Detail: {response.text}")
            return "Sorry, AI assistant is temporarily unable to process the request."

    except Exception as e:
        print(f"[CRITICAL AI EXCEPTION]: {str(e)}")
        return "Sorry, AI assistant is temporarily unavailable."