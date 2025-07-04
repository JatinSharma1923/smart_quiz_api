
from smart_quiz_api.services import scrape_and_generate_quiz

from fastapi import FastAPI, Request, Depends, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security.api_key import APIKeyHeader
from fastapi.websockets import WebSocket
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_429_TOO_MANY_REQUESTS
import logging
import time
import functools
import hashlib
import jinja2
from collections import defaultdict

from routers import quiz_router, user_router,admin_router
from services.rate_limiter import limiter
from services.cache import model_cache
from services.analytics import log_quiz_event

# Include Routers (quiz + user)
app.include_router(quiz_router.router, prefix="/quiz", tags=["Quiz"])
app.include_router(user_router.router, prefix="/user", tags=["User"])
app.include_router(admin_router.router, prefix="/admin", tags=["Admin"])


# Logging Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# App Initialization
app = FastAPI(title="Smart Quiz Master API", version="2.0")

# Jinja2 Prompt Templating Engine
jinja_env = jinja2.Environment(autoescape=True)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key Auth Middleware for AI Routes
API_KEY_NAME = "X-OPENAI-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if not api_key or api_key != "secure-your-openai-api-key":
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")

# Rate Limiting Middleware
@app.middleware("http")
async def enforce_rate_limit(request: Request, call_next):
    client_ip = request.client.host
    if not limiter.allow_request(client_ip):
        return JSONResponse(status_code=HTTP_429_TOO_MANY_REQUESTS, content={"detail": "Rate limit exceeded"})
    return await call_next(request)

# Logging Request Time Middleware
@app.middleware("http")
async def log_request_time(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(f"Request to {request.url.path} took {duration:.3f}s")
    return response

# Exception Logging Middleware
@app.middleware("http")
async def add_exception_logging(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.exception(f"Unhandled error: {str(e)}")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})




# Health Check Route
@app.get("/")
def root():
    return {"message": "✅ Smart Quiz Master API is running!"}

# Auto-Grading Logic + Background Task Logging
@app.post("/quiz/submit")
async def submit_quiz(quiz_data: dict, background_tasks: BackgroundTasks):
    background_tasks.add_task(log_quiz_event, quiz_data)  # Logging
    # TODO: Replace below with real grading logic
    return {"result": "Quiz submitted and being graded"}

# AI Prompt Generation + Caching + Template Rendering
@app.get("/ai/question")
async def get_ai_question(prompt: str, api_key: str = Depends(verify_api_key)):
    cache_key = hashlib.sha256(prompt.encode()).hexdigest()
    if cache_key in model_cache:
        return {"cached": True, "result": model_cache[cache_key]}

    rendered_prompt = jinja_env.from_string("Generate a quiz: {{ prompt }}").render(prompt=prompt)
    ai_result = f"[AI RESPONSE for: {rendered_prompt}]"  # Placeholder for actual OpenAI call
    model_cache[cache_key] = ai_result
    return {"cached": False, "result": ai_result}

# WebSocket for Real-Time Multiplayer (Phase 2)
@app.websocket("/ws/quiz")
async def websocket_quiz(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("🔌 Connected to Real-Time Quiz")
    await websocket.close()

# Global Validation Error Handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()} at {request.url}")
    return JSONResponse(status_code=HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": exc.errors(), "body": exc.body})

# Startup Event
@app.on_event("startup")
async def on_startup():
    logger.info("🚀 API server is starting up...")

# Shutdown Event
@app.on_event("shutdown")
async def on_shutdown():
    logger.info("🛑 API server is shutting down...")
'''
