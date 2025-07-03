
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_quiz(topic, question_type="mcq", difficulty="medium"):
    prompt = f"Create 5 {question_type} questions on {topic} with options, answer, and explanation."
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


'''
import os
import openai
import logging
import redis
from typing import Dict, Literal, Optional, List
from datetime import datetime
from tenacity import retry, wait_random, stop_after_attempt
from dotenv import load_dotenv
from functools import lru_cache
import hashlib
from fastapi import APIRouter, HTTPException, Query  # 🔗 Linking to router

# === Load .env and OpenAI key ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL)
logger = logging.getLogger(__name__)

QuizType = Literal["MCQ", "TF", "IMAGE"]

# === Caching with Redis (for cost+speed) ===
def cache_key(prompt: str) -> str:
    return f"quiz_cache:{hashlib.sha256(prompt.encode()).hexdigest()}"

def get_cached_response(prompt: str) -> Optional[str]:
    key = cache_key(prompt)
    result = redis_client.get(key)
    if result:
        logger.info(f"[Cache Hit] {key}")
        return result.decode("utf-8")
    return None

def set_cached_response(prompt: str, response: str, ttl: int = 3600):
    key = cache_key(prompt)
    redis_client.setex(key, ttl, response)
    logger.info(f"[Cache Store] {key}")

# === PROMPT TEMPLATE LOADING (Prompt Template Selector - plugin ready) ===
@lru_cache(maxsize=10)
def load_prompt_template(quiz_type: QuizType) -> str:
    try:
        path = f"smart_quiz_api/templates/{quiz_type.lower()}.txt"
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        logger.error(f"Prompt template for '{quiz_type}' not found at {path}.")
        raise Exception(f"Prompt template for '{quiz_type}' not found.")
    except Exception as e:
        logger.error(f"Unexpected error loading prompt template: {str(e)}")
        raise

# === PROMPT GENERATOR ===
def render_prompt(topic: str, difficulty: str, quiz_type: QuizType) -> str:
    try:
        template = load_prompt_template(quiz_type)
        return template.replace("{topic}", topic).replace("{difficulty}", difficulty)
    except Exception as e:
        logger.error(f"Error rendering prompt: {str(e)}")
        raise

# === Adaptive Prompt Tuning (based on user level & history) ===
def auto_adjust_difficulty(user_accuracy: float) -> str:
    if user_accuracy >= 80:
        return "hard"
    elif user_accuracy >= 50:
        return "medium"
    return "easy"

# === CALL OPENAI WITH RETRIES ===
@retry(stop=stop_after_attempt(3), wait=wait_random(min=1, max=2))
def call_openai(prompt: str, model: str = "gpt-3.5-turbo") -> str:
    cached = get_cached_response(prompt)
    if cached:
        return cached

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=700,
            temperature=0.7,
        )
        output = response.choices[0].message.content.strip()
        set_cached_response(prompt, output)
        return output
    except Exception as e:
        logger.error(f"OpenAI call failed: {str(e)}")
        raise

# === PARSER: STRUCTURE AI RESPONSE (2 formats) ===
def parse_mcq_response(ai_output: str) -> Dict:
    try:
        lines = ai_output.split("\n")
        data = {"options": {}}
        for line in lines:
            if line.startswith("Q:"):
                data["question"] = line[2:].strip()
            elif line.startswith(tuple("ABCD")):
                data["options"][line[0]] = line[3:].strip()
            elif "Answer:" in line:
                data["correct_option"] = line.split(":", 1)[1].strip()
            elif "Explanation:" in line:
                data["explanation"] = line.split(":", 1)[1].strip()
        data["confidence"] = 0.95
        data["generated_at"] = datetime.utcnow().isoformat()
        return data
    except Exception as e:
        logger.error(f"Failed to parse MCQ response: {str(e)}")
        raise

# === MAIN ENTRY TO GENERATE QUIZ ===
def generate_quiz(topic: str, quiz_type: QuizType = "MCQ", difficulty: str = "medium") -> Dict:
    logger.info(f"🎯 Generating quiz: [{quiz_type}] '{topic}' at {difficulty} level")
    try:
        prompt = render_prompt(topic, difficulty, quiz_type)
        ai_output = call_openai(prompt)
        if quiz_type == "MCQ":
            return parse_mcq_response(ai_output)
        return {"raw_response": ai_output}
    except Exception as e:
        logger.error(f"Quiz generation failed: {str(e)}")
        raise

# === Smart Explanation Simplifier ===
def simplify_explanation(explanation: str) -> str:
    try:
        prompt = f"Explain this like I'm 10: {explanation}"
        return call_openai(prompt)
    except Exception as e:
        logger.error(f"Simplification failed: {str(e)}")
        raise

# === AI Metadata Generator - Tag Generator ===
def generate_tags(question: str) -> List[str]:
    try:
        prompt = f"Give 3 relevant tags (comma-separated) for this question:\n{question}"
        response = call_openai(prompt)
        return [tag.strip() for tag in response.split(",") if tag.strip()]
    except Exception as e:
        logger.error(f"Tag generation failed: {str(e)}")
        return []

# === AI Self-Grading Tool ===
def grade_answer(user_answer: str, correct_option: str, explanation: Optional[str] = "") -> Dict:
    is_correct = user_answer.strip().upper() == correct_option.strip().upper()
    feedback_prompt = (
        f"The correct answer is {correct_option}. The user selected {user_answer}. "
        f"Is it correct? Justify with explanation."
    )
    try:
        ai_feedback = call_openai(feedback_prompt)
    except Exception as e:
        logger.error(f"Grading feedback failed: {str(e)}")
        ai_feedback = "Feedback unavailable."
    return {
        "is_correct": is_correct,
        "feedback": ai_feedback
    }

# === Confidence Calibration/Evaluator ===
def estimate_confidence(quiz_block: str) -> float:
    prompt = f"Rate the confidence in this quiz block on a scale from 0.0 to 1.0:\n{quiz_block}"
    try:
        response = call_openai(prompt)
        return float(response)
    except Exception as e:
        logger.error(f"Confidence estimation failed: {str(e)}")
        return 0.8

# === Router Snippet For Future Linking ===
router = APIRouter()

@router.get("/quiz")
def quiz_generator(
    topic: str = Query(...),
    difficulty: str = Query("medium"),
    quiz_type: QuizType = Query("MCQ")
):
    try:
        quiz = generate_quiz(topic=topic, difficulty=difficulty, quiz_type=quiz_type)
        return {"status": "success", "data": quiz}
    except Exception as e:
        logger.error(f"Quiz generation endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
'''
