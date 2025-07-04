# smart_quiz_api/utils/decorators.py

import functools
import time
from smart_quiz_api.utils.logger import logger

def log_execution(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"▶️ Executing: {func.__name__}")
        result = func(*args, **kwargs)
        logger.info(f"✅ Done: {func.__name__}")
        return result
    return wrapper

def timeit(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        logger.info(f"⏱️ {func.__name__} took {time.time() - start:.2f}s")
        return result
    return wrapper

def safe_handler(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"❌ Exception in {func.__name__}: {str(e)}")
            return None
    return wrapper

