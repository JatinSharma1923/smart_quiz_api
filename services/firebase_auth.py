import firebase_admin
from firebase_admin import credentials, auth
from fastapi import Depends, HTTPException, status, Request
from typing import Optional
import os

# Path to your Firebase service account key
FIREBASE_CRED_PATH = os.getenv("FIREBASE_CRED_PATH", "firebase_service_account.json")

# Only initialize once
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CRED_PATH)
    firebase_admin.initialize_app(cred)

# Dependency for protected routes
def get_current_user(request: Request) -> dict:
    auth_header: Optional[str] = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")

    id_token = auth_header.split(" ")[1]
    try:
        decoded_token = auth.verify_id_token(id_token)
        return {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email"),
            "name": decoded_token.get("name"),
            "picture": decoded_token.get("picture")
        }
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase token")
