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
```bash
git clone https://github.com/JatinSharma1923/smart_quiz_api.git
cd smart_quiz_api
```

### 2. Set up a virtual environment
```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create .env file
Update values for:
```bash
cp .env.example .env
```

Add your keys:
- `OPENAI_API_KEY`
- `FIREBASE_PROJECT_ID`
- `DATABASE_URL`

### 5. Run the API
```bash
uvicorn main:app --reload
```

## 📚 Folder Structure

```
smart_quiz_api/
   ├─ __init__.py
   ├─ main.py
   ├─ database.py
   ├─ models.py
   ├─ schema.py
   ├─ routers/
   │   ├─ __init__.py
   │   ├─ admin_router.py
   │   ├─ quiz_router.py
   │   └─ user_router.py
   ├─ services/
   │   ├─ __init__.py
   │   ├─ firebase_auth.py
   │   ├─ openai_service.py
   │   └─ scraper_service.py
   ├─ templates/        # To be implemented
   │   ├─ image.txt
   │   ├─ mcq.txt
   │   ├─ scraper_prompt.txt
   │   └─ tf.txt
   └─ utils/            # To be implemented
       ├─ decorators.py
       └─ text_utils.py
```


## 📫 Contact

**Made by:** Jatin Sharma  
📬 **Email:** [jatinsharma1923@gmail.com](mailto:jatinsharma1923@gmail.com)  
🌐 **GitHub:** [@JatinSharma1923](https://github.com/JatinSharma1923)


