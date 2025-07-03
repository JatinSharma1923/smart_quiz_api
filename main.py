

from fastapi import FastAPI
from routers import quiz, user

app = FastAPI()

app.include_router(quiz.router, prefix="/quiz", tags=["Quiz"])
app.include_router(user.router, prefix="/user", tags=["User"])

@app.get("/")
def root():
    return {"message": "Welcome to Smart Quiz API"}

