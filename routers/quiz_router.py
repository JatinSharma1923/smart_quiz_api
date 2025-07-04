
from fastapi import (
    APIRouter, Depends, HTTPException, Query, Body,
    BackgroundTasks, Request
)
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from models import (
    Quiz, QuizQuestion, UserAnswer, GradingTask, Feedback
)
from schema import (
    QuizCreate, QuizOut, FeedbackCreate, FeedbackOut,
    UserAnswerOut
)
from database import get_db
from services.openai_service import (
    render_prompt, safe_openai_chat, grade_answer,
    generate_explanation, estimate_confidence
)
from services.scraper_service import generate_quiz_from_url
from services.rate_limiter import limiter

router = APIRouter()


# === Create Quiz ===
@router.post("/", response_model=QuizOut)
def create_quiz(quiz_data: QuizCreate, db: Session = Depends(get_db)):
    quiz = Quiz(
        title=quiz_data.title,
        category=quiz_data.topic,
        difficulty=quiz_data.difficulty,
        duration_seconds=len(quiz_data.questions) * 30,
        start_time=datetime.utcnow()
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    for q in quiz_data.questions:
        question = QuizQuestion(
            quiz_id=quiz.id,
            question_text=q.text,
            options="|".join([a.text for a in q.answers]),
            correct_answer=q.correct_answer,
            question_type=quiz_data.quiz_type.lower(),
            confidence=1.0,
            is_correct=False
        )
        db.add(question)

    db.commit()
    return quiz


# === Get Quiz ===
@router.get("/{quiz_id}", response_model=QuizOut)
def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz


# === List Quizzes ===
@router.get("/", response_model=List[QuizOut])
def list_quizzes(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(Quiz).offset(skip).limit(limit).all()


# === List User Quizzes ===
@router.get("/user/{user_id}", response_model=List[QuizOut])
def list_user_quizzes(user_id: str, db: Session = Depends(get_db)):
    return db.query(Quiz).filter(Quiz.user_id == user_id).all()


# === Update Quiz ===
@router.put("/{quiz_id}", response_model=QuizOut)
def update_quiz(quiz_id: int, updated_data: QuizCreate, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    quiz.title = updated_data.title
    quiz.category = updated_data.topic
    quiz.difficulty = updated_data.difficulty
    quiz.duration_seconds = len(updated_data.questions) * 30
    quiz.updated_at = datetime.utcnow()

    db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz.id).delete()

    for q in updated_data.questions:
        question = QuizQuestion(
            quiz_id=quiz.id,
            question_text=q.text,
            options="|".join([a.text for a in q.answers]),
            correct_answer=q.correct_answer,
            question_type=updated_data.quiz_type.lower(),
            confidence=1.0,
            is_correct=False
        )
        db.add(question)

    db.commit()
    db.refresh(quiz)
    return quiz


# === Delete Quiz ===
@router.delete("/{quiz_id}", response_model=dict)
def delete_quiz(quiz_id: int, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    db.delete(quiz)
    db.commit()
    return {"detail": f"Quiz {quiz_id} deleted successfully"}


# === Generate AI Quiz (with rate limit) ===
@router.get("/generate/ai", response_model=dict)
async def generate_ai_quiz(
    request: Request,
    topic: str = Query(...),
    difficulty: str = Query("medium"),
    quiz_type: str = Query("mcq")
):
    client_ip = request.client.host
    if not limiter.allow_request(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    prompt = render_prompt(topic, difficulty, quiz_type.upper())
    ai_response = safe_openai_chat(prompt)
    return {"generated_quiz": ai_response}


# === Generate Quiz from URL (with rate limit) ===
@router.get("/generate/from-url", response_model=dict)
async def generate_quiz_from_article(
    request: Request,
    url: str = Query(...),
    quiz_type: str = Query("MCQ")
):
    client_ip = request.client.host
    if not limiter.allow_request(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    quiz_data = generate_quiz_from_url(url, quiz_type)
    return quiz_data


# === Submit Quiz Answers ===
@router.post("/{quiz_id}/submit", response_model=List[UserAnswerOut])
def submit_quiz_answers(
    quiz_id: int,
    answers: List[dict] = Body(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    results = []

    for ans in answers:
        question_id = ans["question_id"]
        selected_answer = ans["selected_answer"]
        user_id = ans.get("user_id", "anonymous")

        question = db.query(QuizQuestion).filter(QuizQuestion.id == question_id).first()
        if not question:
            continue

        grading = grade_answer(selected_answer, question.correct_answer)

        user_answer = UserAnswer(
            user_id=user_id,
            question_id=question_id,
            selected_answer=selected_answer,
            is_correct=grading["is_correct"]
        )
        db.add(user_answer)

        grading_task = GradingTask(
            quiz_id=quiz.id,
            user_id=user_id,
            status="completed",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        db.add(grading_task)

        db.commit()
        db.refresh(user_answer)
        results.append(user_answer)

    return results


# === Submit Feedback ===
@router.post("/{quiz_id}/feedback", response_model=FeedbackOut)
def submit_feedback(
    quiz_id: int,
    feedback_data: FeedbackCreate,
    db: Session = Depends(get_db)
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    feedback = Feedback(
        quiz_id=quiz_id,
        user_id="anonymous",
        question_id=None,
        message=feedback_data.message,
        submitted_on=datetime.utcnow()
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


# === AI Explanation for a Quiz ===
@router.get("/{quiz_id}/explain", response_model=dict)
def explain_quiz(quiz_id: int, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz or not quiz.questions:
        raise HTTPException(status_code=404, detail="Quiz or questions not found")

    quiz_text = "\n".join([q.question_text for q in quiz.questions])
    explanation = generate_explanation(quiz_text)
    return {"explanation": explanation}


# === AI Confidence Score ===
@router.get("/{quiz_id}/confidence", response_model=dict)
def confidence_score(quiz_id: int, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz or not quiz.questions:
        raise HTTPException(status_code=404, detail="Quiz or questions not found")

    quiz_text = "\n".join([q.question_text for q in quiz.questions])
    score = estimate_confidence(quiz_text)
    return {"confidence_score": score}
