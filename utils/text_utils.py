# smart_quiz_api/utils/text_utils.py

from pathlib import Path
from typing import Dict

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

def load_template(template_name: str) -> str:
    path = TEMPLATE_DIR / template_name
    if not path.exists():
        raise FileNotFoundError(f"Template '{template_name}' not found.")
    return path.read_text(encoding="utf-8")

def render_template(template_name: str, context: Dict[str, str]) -> str:
    template = load_template(template_name)
    for key, value in context.items():
        template = template.replace(f"{{{key}}}", str(value))
    return template

def truncate_text(text: str, max_words: int = 1500) -> str:
    words = text.split()
    return " ".join(words[:max_words]) + "..." if len(words) > max_words else text

