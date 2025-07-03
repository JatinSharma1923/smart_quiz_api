from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Quiz(Base):
    __tablename__ = 'quizzes'
    id = Column(Integer, primary_key=True)
    question = Column(String)
    answer = Column(String)
    topic = Column(String)
    difficulty = Column(String)
'''

from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Enum
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

    quizzes = relationship("Quiz", back_populates="user")
    badges = relationship("UserBadge", back_populates="user")
    answers = relationship("UserAnswer", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")
    sessions = relationship("SessionLog", back_populates="user")

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
'''
