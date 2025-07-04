# smart_quiz_api/utils/retry_utils.py

from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import openai
from smart_quiz_api.utils.logger import logger

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(openai.error.OpenAIError),
    reraise=True
)
def retry_openai_call(fn, *args, **kwargs):
    logger.info("🔁 Retrying OpenAI call...")
    return fn(*args, **kwargs)
