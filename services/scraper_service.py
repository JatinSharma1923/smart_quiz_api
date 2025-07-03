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
from bs4 import BeautifulSoup
from readability import Document
from textstat import flesch_kincaid_grade
import requests
from urllib.parse import urlparse

# === ENV and Setup ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL)
logger = logging.getLogger(__name__)

QuizType = Literal["MCQ", "TF", "IMAGE"]

# === Helpers: Cache ===
def cache_key_url(url: str, quiz_type: str) -> str:
    return f"url_quiz_cache:{quiz_type}:{hashlib.sha256(url.encode()).hexdigest()}"

def get_cached_quiz(url: str, quiz_type: str) -> Optional[Dict]:
    key = cache_key_url(url, quiz_type)
    result = redis_client.get(key)
    if result:
        logger.info(f"[Cache Hit] Quiz for {url}")
        return eval(result)
    return None

def set_cached_quiz(url: str, quiz_type: str, quiz_data: Dict, ttl: int = 3600):
    key = cache_key_url(url, quiz_type)
    redis_client.setex(key, ttl, str(quiz_data))
    logger.info(f"[Cache Store] Quiz for {url}")

# === Validate URL ===
def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

# === Web Content Scraper ===
def fetch_article_html(url: str) -> str:
    if not is_valid_url(url):
        raise ValueError(f"Invalid URL: {url}")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Failed to fetch URL {url}: {str(e)}")
        raise

def extract_clean_text(html: str) -> str:
    try:
        doc = Document(html)
        summary_html = doc.summary()
        soup = BeautifulSoup(summary_html, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    except Exception as e:
        logger.error(f"Failed to clean HTML: {str(e)}")
        raise

# === Difficulty Estimator from Text ===
def estimate_difficulty(text: str) -> str:
    try:
        grade = flesch_kincaid_grade(text)
        if grade < 6:
            return "easy"
        elif grade < 10:
            return "medium"
        return "hard"
    except Exception as e:
        logger.warning(f"Difficulty estimation failed, defaulting to 'medium': {str(e)}")
        return "medium"

# === Topic Classifier ===
def classify_topic(text: str) -> str:
    try:
        prompt = f"Classify this text into a topic (e.g. History, Science, Tech, etc):\n{text[:500]}"
        response = call_openai(prompt)
        return response.strip()
    except Exception as e:
        logger.error(f"Topic classification failed: {str(e)}")
        return "General Knowledge"

# === OpenAI Caller ===
@retry(stop=stop_after_attempt(3), wait=wait_random(min=1, max=2))
def call_openai(prompt: str, model: str = "gpt-3.5-turbo") -> str:
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=700,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI call failed: {str(e)}")
        raise

# === Scraped Content to Quiz Prompt ===
def generate_quiz_from_url(url: str, quiz_type: QuizType = "MCQ") -> Dict:
    try:
        cached = get_cached_quiz(url, quiz_type)
        if cached:
            return cached

        html = fetch_article_html(url)
        clean_text = extract_clean_text(html)
        topic = classify_topic(clean_text)
        difficulty = estimate_difficulty(clean_text)

        # Truncate smartly
        snippet = clean_text[:clean_text.rfind(".", 1400, 1600)+1] or clean_text[:1500]

        # Render prompt and generate quiz
        prompt = f"Generate a {quiz_type} quiz for this topic: {topic}, difficulty: {difficulty}. Use this content:\n{snippet}"
        quiz = call_openai(prompt)

        result = {
            "topic": topic,
            "difficulty": difficulty,
            "quiz_type": quiz_type,
            "source_url": url,
            "scraped_at": datetime.utcnow().isoformat(),
            "content_excerpt": snippet,
            "quiz": quiz,
        }

        set_cached_quiz(url, quiz_type, result)
        return result
    except Exception as e:
        logger.error(f"Quiz generation from URL failed: {str(e)}")
        raise

# === Final Entrypoint ===
def scrape_and_generate_quiz(url: str, quiz_type: QuizType = "MCQ") -> Dict:
    return generate_quiz_from_url(url, quiz_type)
