# app/dependencies.py
#	dependencies.py = 「エンドポイントで共通して必要なユーザー/DB/権限などを注入する場所」
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
        user = User(
            id=1,
            name="Dummy", 
            email="dummy@u-aizu.ac.jp",
            role="student"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user