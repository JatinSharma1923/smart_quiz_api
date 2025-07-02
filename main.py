from fastapi import FastAPI
from routers import quiz, user

app = FastAPI()
app.include_router(quiz.router)
app.include_router(user.router)
