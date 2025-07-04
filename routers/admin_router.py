from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schema import (
    FeedbackOut, ErrorLogOut, SessionLogOut, GradingTaskOut,
    APIKeyOut, HealthCheckLogOut, PromptCacheOut, LogOut
)
from models import (
    Feedback, ErrorLog, SessionLog, GradingTask, APIKey,
    HealthCheckLog, PromptCache, User, Quiz, RequestLog
)
import redis
import os
import openai
from dotenv import load_dotenv
from services.firebase_auth import get_current_user

def verify_admin_user(user: User = Depends(get_current_user)):
    if not user.is_admin:  # you'd need to add this to model
        raise HTTPException(status_code=403, detail="Admins only")
    return user


# === Load env variables ===
load_dotenv()
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "changeme")

# === Redis Connection ===
redis_client = redis.Redis.from_url(REDIS_URL)

# === Security Dependency ===
def verify_admin_key(x_admin_key: str = Header(...)):
    if x_admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized access to admin routes")

# === Router Setup with global dependency ===
router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(verify_admin_key)]
)

# === System Stats ===
@router.get("/stats", response_model=dict,dependencies=[Depends(verify_admin_user)])
def get_stats(db: Session = Depends(get_db)):
    return {
        "total_users": db.query(User).count(),
        "total_quizzes": db.query(Quiz).count(),
        "total_feedback": db.query(Feedback).count(),
        "total_errors": db.query(ErrorLog).count(),
        "grading_tasks": db.query(GradingTask).count(),
        "sessions": db.query(SessionLog).count()
    }

# === Feedback Logs ===
@router.get("/feedbacks", response_model=List[FeedbackOut])
def list_feedbacks(db: Session = Depends(get_db)):
    return db.query(Feedback).order_by(Feedback.submitted_on.desc()).limit(100).all()

# === Error Logs ===
@router.get("/errors", response_model=List[ErrorLogOut])
def list_errors(db: Session = Depends(get_db)):
    return db.query(ErrorLog).order_by(ErrorLog.occurred_at.desc()).limit(100).all()

# === Session Logs ===
@router.get("/sessions", response_model=List[SessionLogOut])
def list_sessions(db: Session = Depends(get_db)):
    return db.query(SessionLog).order_by(SessionLog.login_time.desc()).limit(100).all()

# === Grading Tasks ===
@router.get("/grading-tasks", response_model=List[GradingTaskOut])
def list_grading_tasks(db: Session = Depends(get_db)):
    return db.query(GradingTask).order_by(GradingTask.started_at.desc()).limit(100).all()

# === API Keys ===
@router.get("/api-keys", response_model=List[APIKeyOut])
def list_api_keys(db: Session = Depends(get_db)):
    return db.query(APIKey).order_by(APIKey.created_at.desc()).all()

# === Toggle API Key ===
@router.patch("/api-keys/{key}/toggle", response_model=APIKeyOut)
def toggle_api_key(key: str, db: Session = Depends(get_db)):
    api_key = db.query(APIKey).filter(APIKey.key == key).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    api_key.is_active = not api_key.is_active
    db.commit()
    db.refresh(api_key)
    return api_key

# === Health Check Logs ===
@router.get("/health", response_model=List[HealthCheckLogOut])
def get_health_logs(db: Session = Depends(get_db)):
    return db.query(HealthCheckLog).order_by(HealthCheckLog.checked_at.desc()).limit(50).all()

# === Prompt Cache ===
@router.get("/prompt-cache", response_model=List[PromptCacheOut])
def get_prompt_cache(db: Session = Depends(get_db)):
    return db.query(PromptCache).order_by(PromptCache.created_at.desc()).limit(100).all()

# === Request Logs ===
@router.get("/requests", response_model=List[LogOut])
def get_request_logs(db: Session = Depends(get_db)):
    return db.query(RequestLog).order_by(RequestLog.timestamp.desc()).limit(100).all()

# === Clear Redis Cache ===
@router.delete("/cache/clear", response_model=dict)
def clear_redis_cache():
    redis_client.flushdb()
    return {"detail": "Redis cache cleared successfully."}

# === OpenAI Status Test ===
@router.get("/openai/status", response_model=dict)
def openai_status_check():
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, are you online?"}]
        )
        return {"status": "online", "message": response.choices[0].message.content.strip()}
    except Exception as e:
        return {"status": "offline", "error": str(e)}
