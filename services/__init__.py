
from .openai_service import (
    render_prompt,
    call_openai,
    classify_topic,
    generate_explanation,
    generate_tags,
    grade_answer,
    estimate_confidence,
)


# smart_quiz_api/services/__init__.py

from .scraper_service import scrape_and_generate_quiz, generate_quiz_from_url
