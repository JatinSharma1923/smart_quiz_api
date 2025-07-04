import os
from fastapi import Depends, HTTPException, Request, status
from firebase_admin import auth, credentials, initialize_app
import firebase_admin
from sqlalchemy.orm import Session
from uuid import uuid4

from models import User
from database import get_db
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Path to Firebase Admin SDK service account JSON
FIREBASE_CRED_PATH = os.getenv("FIREBASE_CRED_PATH", "firebase_service_account.json")

# Initialize Firebase Admin SDK (only once)
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(FIREBASE_CRED_PATH)
        initialize_app(cred)
    except Exception as e:
        raise RuntimeError(f"❌ Firebase initialization failed: {e}")

# Main auth dependency
def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header"
        )

    token = auth_header.split(" ")[1]

    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token["uid"]
        email = decoded_token.get("email", "")
        name = decoded_token.get("name", "")
        picture = decoded_token.get("picture", "")

        # Check or create user in database
        user = db.query(User).filter(User.firebase_uid == uid).first()
        if not user:
            user = User(
                id=str(uuid4()),
                firebase_uid=uid,
                email=email,
                username=name or email.split("@")[0],
                hashed_password=None,
                profile_picture=picture if hasattr(User, "profile_picture") else None
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        return user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token"
        )
