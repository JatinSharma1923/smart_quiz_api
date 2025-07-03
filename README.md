# Smart Quiz Backend
# 🧠 Smart Quiz API

The **Smart Quiz API** is a FastAPI-powered backend for generating, managing, and grading AI-powered quizzes. It integrates with OpenAI's GPT-4o, Firebase Authentication, and PostgreSQL, making it suitable for interview prep, UPSC, SSC, cybersecurity learning, and more.

---

## 🚀 Features

- 🔐 Firebase User Authentication
- 🤖 AI-generated quizzes from prompts or URLs (OpenAI GPT-4o)
- 🧠 Multiple question types (MCQ, True/False, Image-based)
- 🗂️ Quiz categorization by topic, difficulty, and tags
- 📊 User tracking, streaks, badges, and analytics
- 🛡️ Rate limiting, API keys, logging & error tracing
- 🧰 Fully modular FastAPI structure with routers, services, and templates

---

## 🛠️ Tech Stack

- **Python 3.11+**
- **FastAPI**
- **PostgreSQL**
- **SQLAlchemy ORM**
- **Firebase Auth**
- **OpenAI GPT-4o**
- **Redis (for caching/queues, optional)**

---

## ⚙️ Setup Guide

### 1. Clone the repo
  git clone https://github.com/JatinSharma1923/smart_quiz_api.git
  cd smart_quiz_api

###2. Set up a virtual environment
  python -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate

###3. Install dependencies
  pip install -r requirements.txt

###4. Create .env file
  Update values for:
  cp .env.example .env
  OPENAI_API_KEY
  FIREBASE_PROJECT_ID
  DATABASE_URL

###5. Run the API
  uvicorn main:app --reload

📚 Folder Structure
  smart_quiz_api/
  ├── routers/           # FastAPI route controllers
  ├── services/          # Business logic (OpenAI, scraping, quiz logic)
  ├── templates/         # Prompt templates
  ├── auth/              # Firebase Auth integration
  ├── models.py          # SQLAlchemy models
  ├── schemas.py         # Pydantic schemas
  ├── database.py        # DB session & setup
  ├── main.py            # FastAPI app entry point
  └── .env.example       # Sample config file



📫 Contact
  Made by Jatin Sharma
  📬 Email: jatinsharma1923@gmail.com
  🌐 GitHub: @JatinSharma1923



