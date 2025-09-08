# app/routers/auth.py

import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, _ensure_user_exists
from src.models.user import User as UserModel

# Firebase Admin SDK（初期化は app/core/firebase.py 側で実施）
try:
    from firebase_admin import auth as firebase_auth  # type: ignore
    from app.core.firebase import *  # noqa: F401  初期化の副作用
    _FIREBASE_AVAILABLE = True
except Exception:
    _FIREBASE_AVAILABLE = False

router = APIRouter(prefix="/auth", tags=["auth"])

SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "session")


@router.post("/firebase-login")
async def firebase_login(request: Request, db: Session = Depends(get_db)):
    """
    フロントから { idToken } を受け取り、Firebase で検証。
    DBにユーザーを upsert し、セッションクッキー（USER:{id}）を発行して 200 を返す。
    """
    if not _FIREBASE_AVAILABLE:
        raise HTTPException(status_code=500, detail="Firebase Admin SDK is not available")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    id_token: Optional[str] = (body or {}).get("idToken")
    if not id_token:
        raise HTTPException(status_code=400, detail="idToken is required")

    try:
        # 多少の時刻ズレを許容（最大60秒）
        decoded = firebase_auth.verify_id_token(id_token, clock_skew_seconds=60)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid ID token: {str(e)}")

    # Firebase payload から情報抽出
    email = decoded.get("email")
    name = decoded.get("name") or "Unknown"
    picture = decoded.get("picture")
    if not email:
        raise HTTPException(status_code=400, detail="Email not provided by identity provider")

    # DB upsert（role は保持）
    user = _ensure_user_exists(db, None, name=name, email=email, avatar=picture)

    # セッションクッキー発行
    session_value = f"USER:{user.id}"
    resp = JSONResponse(
        status_code=200,
        content={
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "avatar": getattr(user, "avatar", None),
            "role": getattr(user, "role", "student"),
        },
    )
    resp.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_value,
        httponly=True,
        secure=False,   # 本番は True（HTTPS 前提）
        samesite="lax", # 本番でクロスサイト必要なら "none" + secure=True
        max_age=60 * 60 * 24 * 7,  # 7日
        path="/",
    )
    return resp


@router.post("/logout")
def logout():
    """セッションクッキーを削除。"""
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return resp


@router.get("/me")
def get_me(user: UserModel = Depends(get_current_user)):
    """現在ログイン中のユーザー情報を返す。"""
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "avatar": getattr(user, "avatar", None),
        "role": getattr(user, "role", "student"),
    }