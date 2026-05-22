from pydantic import BaseModel, EmailStr, Field
from typing import List, Literal

# ==========================================
# Auth Models
# ==========================================

class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: Literal["student", "admin"]
    roll_number: str = Field(..., min_length=1, max_length=50)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: Literal["student", "admin"]

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str

# ==========================================
# Skill Models
# ==========================================

class AddSkillRequest(BaseModel):
    skill_id: int
    proficiency_level: Literal["Beginner", "Intermediate", "Advanced"]
    proficiency_percent: int = Field(..., ge=0, le=100)

class DeleteSkillRequest(BaseModel):
    user_skill_id: int

# ==========================================
# Task Models
# ==========================================

class ApplyTaskRequest(BaseModel):
    task_id: int

class SubmitProofRequest(BaseModel):
    app_id: int
    submission_text: str = Field(..., min_length=1)

# ==========================================
# AI Chat Model
# ==========================================

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)

class ChatResponse(BaseModel):
    reply: str

# ==========================================
# Admin Models
# ==========================================

class CreateTaskRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: str
    # Fixed to precisely match database strict ENUM criteria
    difficulty: Literal["Beginner", "Intermediate", "Advanced"]
    reward_xp: int = Field(..., gt=0)
    required_skills: List[int]
    # Place this at the end of your schemas.py file:

class ReviewRequest(BaseModel):
    application_id: int
    status: Literal["approved", "rejected"]