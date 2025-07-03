from fastapi import APIRouter
from services.openai_service import generate_quiz

router = APIRouter()

@router.get("/generate")
def generate(topic: str, difficulty: str = "medium", q_type: str = "mcq"):
    return {"quiz": generate_quiz(topic, q_type, difficulty)}

