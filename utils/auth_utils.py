# smart_quiz_api/utils/auth_utils.py

import firebase_admin
from firebase_admin import auth, credentials
from fastapi import HTTPException

# This assumes firebase_admin.initialize_app() is called somewhere globally

def verify_token(id_token: str) -> dict:
    try:
        decoded = auth.verify_id_token(id_token)
        return decoded
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

def get_user_email(decoded_token: dict) -> str:
    return decoded_token.get("email", "unknown@user.com")
