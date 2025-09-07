# app/dependencies.py

import os
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from src.models.user import User

SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "session")

def _ensure_user_exists(db: Session, user_id: int | None = None, *, name: str, email: str, avatar: str | None = None):
    if user_id is not None:
        u = db.query(User).filter(User.id == user_id).first()
        if u:
            if name and u.name != name:
                u.name = name
            db.commit()
            db.refresh(u)
            return u
        u = User(id=user_id, name=name, email=email, role="student")
        db.add(u); db.commit(); db.refresh(u)
        return u

    u = db.query(User).filter(User.email == email).first()
    if not u:
        u = User(name=name, email=email, role="student")
        db.add(u); db.commit(); db.refresh(u)
    return u

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(SESSION_COOKIE_NAME)

    # 1) Firebase セッション（/auth/firebase-login で発行）
    if token and isinstance(token, str) and token.startswith("USER:"):
        try:
            user_id = int(token.split(":", 1)[1])
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = _ensure_user_exists(db, user_id=user_id, name="User", email=f"user{user_id}@local")
        return user

    # 2) 既存のダミー JWT（古い挙動の互換、必要なら残す / 不要なら消す）
    if token == "DUMMY_JWT_FOR_LOCAL":
        user = db.query(User).filter(User.id == 1).first()
        if not user:
            user = _ensure_user_exists(db, user_id=1, name="Dummy", email="dummy@u-aizu.ac.jp")
        return user

    # 3) 未認証は常に 401（開発でもダミー返却をしない）
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")