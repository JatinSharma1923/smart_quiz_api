

import os
import logging
import hashlib
from typing import Dict, Optional, List
from datetime import datetime
from dotenv import load_dotenv
from functools import lru_cache
import redis
from tenacity import retry, wait_random, stop_after_attempt
import openai
from typing import Literal


# === Custom Exceptions ===
class PromptTemplateNotFound(Exception):
    """Raised when a quiz type template file is missing."""
    pass

class OpenAIResponseError(Exception):
    """Raised when OpenAI returns an invalid or incomplete response."""
    pass


# === ENV and Setup ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

QuizType = Literal["MCQ", "TF", "IMAGE"]

# === Prompt Template Loader ===
@lru_cache(maxsize=10)
def load_prompt_template(quiz_type: QuizType) -> str:
    path = f"smart_quiz_api/templates/{quiz_type.lower()}.txt"
    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        logger.exception(f"Prompt template not found at: {path}")
        raise Exception(f"Prompt template for '{quiz_type}' not found.")
    except Exception as e:
        logger.exception(f"Unexpected error loading prompt template: {e}")
        raise

# === Prompt Renderer ===
def render_prompt(topic: str, difficulty: str, quiz_type: QuizType) -> str:
    try:
        template = load_prompt_template(quiz_type)
        return template.replace("{topic}", topic).replace("{difficulty}", difficulty)
    except Exception as e:
        logger.exception(f"Error rendering prompt: {e}")
        raise

# === Redis Caching Utilities ===
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

# === OpenAI Call with Retry ===
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
        result = response.choices[0].message.content.strip()
        # LOGGING USAGE HERE
        usage = response.get("usage", {})
        logger.info(f"OpenAI API Usage — Prompt Tokens: {usage.get('prompt_tokens')}, Completion Tokens: {usage.get('completion_tokens')}, Total Tokens: {usage.get('total_tokens')}")

        set_cached_response(prompt, result)
        return result
    except Exception as e:
        logger.exception("OpenAI call failed")
        raise

# ✅ Safe Wrapper for Exception Handling
def safe_openai_chat(prompt: str, model: str = "gpt-3.5-turbo", max_tokens=700, temperature=0.7) -> str:
    try:
        return call_openai(prompt, model=model)
    except openai.error.OpenAIError as oe:
        logger.error(f"OpenAI API error: {oe}")
        raise OpenAIResponseError("OpenAI returned an unexpected error.")


# === Topic Classifier ===
def classify_topic(content: str) -> str:
    prompt = f"Classify the following content into a topic (e.g., Science, History, Tech, etc):\n\n{content[:1000]}"
    try:
        return call_openai(prompt)
    except Exception as e:
        logger.warning(f"Topic classification failed: {e}")
        return "General Knowledge"

# === Explanation Generator ===
def generate_explanation(quiz_text: str) -> str:
    prompt = f"Explain each correct answer in the following quiz in 1-2 beginner-friendly sentences:\n\n{quiz_text}"
    return call_openai(prompt)

# === AI Metadata Generator - Tag Generator ===
def generate_tags(question: str) -> List[str]:
    try:
        prompt = f"Give 3 relevant tags (comma-separated) for this question:\n{question}"
        response = call_openai(prompt)
        return [tag.strip() for tag in response.split(",") if tag.strip()]
    except Exception as e:
        logger.error(f"Tag generation failed: {e}")
        return []

# === AI Self-Grading Tool ===
def grade_answer(user_answer: str, correct_option: str, explanation: Optional[str] = "") -> Dict:
    is_correct = user_answer.strip().upper() == correct_option.strip().upper()
    feedback_prompt = (
        f"The correct answer is {correct_option}. The user selected {user_answer}. "
        f"Is it correct? Justify with explanation."
    )
    try:
        feedback = call_openai(feedback_prompt)
    except Exception as e:
        logger.error(f"Grading feedback failed: {e}")
        feedback = "Feedback unavailable."
    return {
        "is_correct": is_correct,
        "feedback": feedback
    }

# === Confidence Evaluator ===
def estimate_confidence(quiz_block: str) -> float:
    prompt = f"Rate the confidence in this quiz block on a scale from 0.0 to 1.0:\n{quiz_block}"
    try:
        response = call_openai(prompt)
        return min(max(float(response), 0.0), 1.0)
    except Exception as e:
        logger.error(f"Confidence estimation failed: {e}")
        return 0.8

