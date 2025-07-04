# smart_quiz_api/schemas.py

from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime


### === User ===
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str
    full_name: str
    firebase_uid: Optional[str] = None
    profile_picture: Optional[str] = None
    class Config:
        orm_mode = True


### === Answer ===
class AnswerCreate(BaseModel):
    text: str
    is_correct: Optional[bool] = False

class AnswerOut(BaseModel):
    id: int
    text: str
    is_correct: bool
    class Config:
        orm_mode = True


### === Question ===
class QuestionCreate(BaseModel):
    text: str
    correct_answer: str
    answers: List[AnswerCreate]

class QuestionOut(BaseModel):
    id: int
    text: str
    correct_answer: str
    answers: List[AnswerOut]
    class Config:
        orm_mode = True


### === Quiz ===
class QuizCreate(BaseModel):
    title: str
    topic: str
    difficulty: str
    quiz_type: str
    questions: List[QuestionCreate]

class QuizOut(BaseModel):
    id: int
    title: str
    topic: str
    difficulty: str
    quiz_type: str
    created_at: datetime
    questions: List[QuestionOut]
    class Config:
        orm_mode = True


### === Badge ===
class BadgeOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    class Config:
        orm_mode = True


### === Feedback ===
class FeedbackCreate(BaseModel):
    message: str
    rating: Optional[int] = 5

class FeedbackOut(BaseModel):
    id: int
    message: str
    rating: Optional[int]
    created_at: datetime
    class Config:
        orm_mode = True


### === API Key ===
class APIKeyOut(BaseModel):
    key_id: str
    user_id: int
    is_active: bool
    created_at: datetime
    class Config:
        orm_mode = True


### === Generic Log ===
class LogOut(BaseModel):
    id: int
    event_type: str
    detail: str
    timestamp: datetime
    class Config:
        orm_mode = True
# === New Additions to schema.py ===

class UserAnswerOut(BaseModel):
    id: int
    question_id: int
    selected_answer: str
    is_correct: bool
    class Config:
        orm_mode = True

class SessionLogOut(BaseModel):
    id: int
    login_time: datetime
    logout_time: Optional[datetime]
    ip_address: str
    device_info: str
    class Config:
        orm_mode = True

class WebSocketSessionOut(BaseModel):
    id: int
    connection_time: datetime
    disconnect_time: Optional[datetime]
    client_ip: str
    class Config:
        orm_mode = True

class GradingTaskOut(BaseModel):
    id: int
    quiz_id: int
    user_id: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    class Config:
        orm_mode = True

class PromptTemplateOut(BaseModel):
    id: int
    name: str
    context: str
    template_text: str
    created_by: str
    created_at: datetime
    class Config:
        orm_mode = True

class PromptCacheOut(BaseModel):
    id: int
    prompt_hash: str
    response_text: str
    created_at: datetime
    class Config:
        orm_mode = True

class ErrorLogOut(BaseModel):
    id: int
    error_type: str
    message: str
    stack_trace: str
    occurred_at: datetime
    class Config:
        orm_mode = True

class HealthCheckLogOut(BaseModel):
    id: int
    service: str
    status: str
    checked_at: datetime
    response_time_ms: float
    class Config:
        orm_mode = True

