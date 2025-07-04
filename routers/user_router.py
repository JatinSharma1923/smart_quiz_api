from fastapi import APIRouter, Depends, HTTPException, Body
from services.firebase_auth import get_current_user
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from uuid import uuid4
import bcrypt

from database import get_db
from models import User, UserAnswer, UserBadge, SessionLog
from schema import (
    UserCreate, UserOut,
    UserAnswerOut, SessionLogOut, BadgeOut
)

router = APIRouter(
    prefix="/user",
    tags=["User"]
)

# === Utility: Hash and verify ===
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))


# === Register a new user ===
@router.post("/register", response_model=UserOut)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        id=str(uuid4()),
        email=user_data.email,
        username=user_data.full_name,
        hashed_password=hash_password(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# === User login ===
@router.post("/login", response_model=UserOut)
def login_user(email: str = Body(...), password: str = Body(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.is_deleted:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    return user


# === Get user profile ===
@router.get("/{user_id}", response_model=UserOut)
def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.is_deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# === Update user profile ===
@router.put("/{user_id}", response_model=UserOut)
def update_user_profile(user_id: str, update: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.email = update.email
    user.username = update.full_name
    user.hashed_password = hash_password(update.password)
    db.commit()
    db.refresh(user)
    return user


# === Change password ===
@router.patch("/{user_id}/change-password", response_model=dict)
def change_password(
    user_id: str,
    old_password: str = Body(...),
    new_password: str = Body(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not verify_password(old_password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect current password")
    user.hashed_password = hash_password(new_password)
    db.commit()
    return {"detail": "Password changed successfully"}


# === Soft delete user account ===
@router.delete("/{user_id}", response_model=dict)
def delete_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.is_deleted:
        raise HTTPException(status_code=404, detail="User not found or already deleted")
    user.is_deleted = True
    db.commit()
    return {"detail": "User account soft-deleted"}


# === Reactivate user account ===
@router.patch("/{user_id}/reactivate", response_model=dict)
def reactivate_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_deleted = False
    db.commit()
    return {"detail": "User account reactivated"}


# === Get user's quiz answers ===
@router.get("/{user_id}/answers", response_model=List[UserAnswerOut])
def get_user_answers(user_id: str, db: Session = Depends(get_db)):
    return db.query(UserAnswer).filter(UserAnswer.user_id == user_id).all()


# === Get user's earned badges ===
@router.get("/{user_id}/badges", response_model=List[BadgeOut])
def get_user_badges(user_id: str, db: Session = Depends(get_db)):
    badge_joins = db.query(UserBadge).filter(UserBadge.user_id == user_id).all()
    return [ub.badge for ub in badge_joins]


# === Get user's login sessions ===
@router.get("/{user_id}/sessions", response_model=List[SessionLogOut])
def get_user_sessions(user_id: str, db: Session = Depends(get_db)):
    return db.query(SessionLog).filter(SessionLog.user_id == user_id).order_by(SessionLog.login_time.desc()).limit(50).all()


# === Get user stats (quizzes taken, avg score, streak) ===
@router.get("/{user_id}/stats", response_model=dict)
def get_user_stats(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "quizzes_taken": user.total_quizzes_taken,
        "average_score": user.average_score,
        "streak": user.streak
    }

