import os
import logging
import hashlib
import json
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

# === Load ENV ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# === Constants ===
QuizType = Literal["MCQ", "TF", "IMAGE"]
MAX_SNIPPET = 1600
MIN_SNIPPET = 1400
DEFAULT_MODEL = os.getenv("SCRAPER_MODEL", "gpt-3.5-turbo")
CACHE_TTL = 3600

# === Cache Utilities ===
def cache_key_url(url: str, quiz_type: str) -> str:
    return f"url_quiz_cache:{quiz_type}:{hashlib.sha256(url.encode()).hexdigest()}"

def get_cached_quiz(url: str, quiz_type: str) -> Optional[Dict]:
    key = cache_key_url(url, quiz_type)
    result = redis_client.get(key)
    if result:
        logger.info(f"[Cache Hit] Quiz for {url}")
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            logger.warning("Failed to decode cached quiz data")
            return None
    return None

def set_cached_quiz(url: str, quiz_type: str, quiz_data: Dict, ttl: int = CACHE_TTL):
    key = cache_key_url(url, quiz_type)
    redis_client.setex(key, ttl, json.dumps(quiz_data))
    logger.info(f"[Cache Store] Quiz for {url}")

# === URL and Content Utilities ===
def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

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

# === Difficulty & Topic Estimation ===
def estimate_difficulty(text: str) -> str:
    try:
        if len(text.split()) < 100:
            return "easy"
        grade = flesch_kincaid_grade(text)
        if grade < 6:
            return "easy"
        elif grade < 10:
            return "medium"
        return "hard"
    except Exception as e:
        logger.warning(f"Difficulty estimation failed, defaulting to 'medium': {str(e)}")
        return "medium"

def classify_topic(text: str) -> str:
    try:
        prompt = f"Classify this text into a topic (e.g. History, Science, Tech, etc):\n{text[:500]}"
        response = call_openai(prompt)
        return response.strip()
    except Exception as e:
        logger.error(f"Topic classification failed: {str(e)}")
        return "General Knowledge"

# === OpenAI Wrapper ===
@retry(stop=stop_after_attempt(3), wait=wait_random(min=1, max=2))
def call_openai(prompt: str, model: str = DEFAULT_MODEL) -> str:
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

# === Quiz Generator Core ===
def generate_quiz_from_url(url: str, quiz_type: QuizType = "MCQ") -> Dict:
    try:
        cached = get_cached_quiz(url, quiz_type)
        if cached:
            return cached

        html = fetch_article_html(url)
        clean_text = extract_clean_text(html)
        topic = classify_topic(clean_text)
        difficulty = estimate_difficulty(clean_text)

        # Trim snippet cleanly
        end_idx = clean_text.rfind(".", MIN_SNIPPET, MAX_SNIPPET)
        snippet = clean_text[:end_idx + 1] if end_idx != -1 else clean_text[:1500]

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
        logger.info(f"[Quiz Generated] Topic: {topic}, Difficulty: {difficulty}, Length: {len(snippet)}")
        logger.debug(f"[Quiz Metadata] Topic: {topic}, Difficulty: {difficulty}, Snippet Size: {len(snippet)}")
        return result
    except Exception as e:
        logger.error(f"Quiz generation from URL failed: {str(e)}")
        raise

# === CLI Entrypoint for Testing ===
if __name__ == "__main__":
    test_url = "https://www.bbc.com/news/science-environment-68903401"
    quiz_data = generate_quiz_from_url(test_url, quiz_type="MCQ")
    print("\n🧠 Generated Quiz:\n")
    print(quiz_data["quiz"])

