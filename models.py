

from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Enum, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Timestamp mixin for created_at and updated_at
class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# User model
class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    total_quizzes_taken = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    streak = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)
    firebase_uid = Column(String, unique=True, nullable=True)
    profile_picture = Column(String, nullable=True) 
    quizzes = relationship("Quiz", back_populates="user")
    badges = relationship("UserBadge", back_populates="user")
    answers = relationship("UserAnswer", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")
    sessions = relationship("SessionLog", back_populates="user")
    request_logs = relationship("RequestLog", back_populates="user")
    websocket_sessions = relationship("WebSocketSession", back_populates="user")

# Quiz model
class Quiz(Base, TimestampMixin):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    category = Column(String)
    difficulty = Column(Enum("easy", "medium", "hard", name="difficulty_enum"))
    user_id = Column(String, ForeignKey("users.id"))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    duration_seconds = Column(Integer)
    source_url = Column(String)
    scraped_at = Column(DateTime)

    user = relationship("User", back_populates="quizzes")
    questions = relationship("QuizQuestion", back_populates="quiz")
    feedbacks = relationship("Feedback", back_populates="quiz")
    grading_tasks = relationship("GradingTask", back_populates="quiz")

# QuizQuestion model
class QuizQuestion(Base, TimestampMixin):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    question_text = Column(String)
    options = Column(String)
    correct_answer = Column(String)
    question_type = Column(Enum("mcq", "true_false", "image", name="question_type_enum"))
    confidence = Column(Float)
    is_correct = Column(Boolean)

    quiz = relationship("Quiz", back_populates="questions")
    answers = relationship("UserAnswer", back_populates="question")
    feedbacks = relationship("Feedback", back_populates="question")

# UserAnswer model
class UserAnswer(Base, TimestampMixin):
    __tablename__ = "user_answers"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    question_id = Column(Integer, ForeignKey("quiz_questions.id"))
    selected_answer = Column(String)
    is_correct = Column(Boolean)

    user = relationship("User", back_populates="answers")
    question = relationship("QuizQuestion", back_populates="answers")

# Badge model
class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    icon_url = Column(String)

# UserBadge model
class UserBadge(Base):
    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    badge_id = Column(Integer, ForeignKey("badges.id"))
    awarded_on = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="badges")

# Feedback model
class Feedback(Base, TimestampMixin):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    question_id = Column(Integer, ForeignKey("quiz_questions.id"))
    message = Column(String)
    submitted_on = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="feedbacks")
    quiz = relationship("Quiz", back_populates="feedbacks")
    question = relationship("QuizQuestion", back_populates="feedbacks")

# Session log model
class SessionLog(Base):
    __tablename__ = "session_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    login_time = Column(DateTime, default=datetime.utcnow)
    logout_time = Column(DateTime)
    ip_address = Column(String)
    device_info = Column(String)

    user = relationship("User", back_populates="sessions")

# API Key model
class APIKey(Base):
    __tablename__ = "api_keys"

    key = Column(String, primary_key=True)
    owner = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    rate_limit = Column(Integer)

# Rate Limit Log
class RateLimitLog(Base):
    __tablename__ = "rate_limit_logs"

    id = Column(Integer, primary_key=True)
    ip_address = Column(String)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    api_key = Column(String, ForeignKey("api_keys.key"), nullable=True)
    request_time = Column(DateTime, default=datetime.utcnow)

# Request Log
class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    path = Column(String)
    method = Column(String)
    status_code = Column(Integer)
    duration_ms = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="request_logs")

# Error Log
class ErrorLog(Base):
    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True)
    error_type = Column(String)
    message = Column(Text)
    stack_trace = Column(Text)
    occurred_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)

# Background Task Queue
class BackgroundTaskQueue(Base):
    __tablename__ = "background_tasks"

    id = Column(Integer, primary_key=True)
    task_name = Column(String)
    payload = Column(Text)
    status = Column(Enum("pending", "in_progress", "completed", "failed", name="task_status_enum"))
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

# WebSocket Session
class WebSocketSession(Base):
    __tablename__ = "websocket_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    connection_time = Column(DateTime, default=datetime.utcnow)
    disconnect_time = Column(DateTime)
    client_ip = Column(String)

    user = relationship("User", back_populates="websocket_sessions")

# Prompt Template
class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    context = Column(String)
    template_text = Column(Text)
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Prompt Cache
class PromptCache(Base):
    __tablename__ = "prompt_cache"

    id = Column(Integer, primary_key=True)
    prompt_hash = Column(String, unique=True)
    response_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# Health Check Log
class HealthCheckLog(Base):
    __tablename__ = "health_check_logs"

    id = Column(Integer, primary_key=True)
    service = Column(String)
    status = Column(Enum("healthy", "degraded", "down", name="health_status_enum"))
    checked_at = Column(DateTime, default=datetime.utcnow)
    response_time_ms = Column(Float)

# Grading Task
class GradingTask(Base):
    __tablename__ = "grading_tasks"

    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    user_id = Column(String, ForeignKey("users.id"))
    status = Column(Enum("pending", "in_progress", "completed", "error", name="grading_status_enum"))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)

    quiz = relationship("Quiz", back_populates="grading_tasks")

