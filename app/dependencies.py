# app/dependencies.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from src.models.user import User  # ← ユーザーモデルの場所に応じて修正！

def get_current_user(db: Session = Depends(get_db)):
    """
    TODO: 本来はJWTを検証してユーザーを取得する。
    今は暫定で id=1 のユーザーを返す。
    """
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found (dummy auth)",
        )
    return user