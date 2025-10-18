# app/dependencies.py

import os
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from src.models.user import User

SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "session")

def _ensure_user_exists(
    db: Session,
    user_id: int | None = None,
    *,
    name: str,
    email: str,
    avatar: str | None = None,
) -> User:
    """
    Firebase ログイン時などに DB のユーザーを安全に upsert する共通関数。
    - 既存ユーザーの role は上書きしない
    - display 情報（name, avatar）は更新する
    """
    if user_id is not None:
        u = db.query(User).filter(User.id == user_id).first()
        if u:
            changed = False
            if name and u.name != name:
                u.name = name; changed = True
            if avatar is not None and hasattr(u, "avatar") and u.avatar != avatar:
                u.avatar = avatar; changed = True
            if changed:
                db.commit(); db.refresh(u)
            return u

        u = User(id=user_id, name=name, email=email, role="student")
        if avatar is not None and hasattr(u, "avatar"):
            u.avatar = avatar
        db.add(u); db.commit(); db.refresh(u)
        return u

    # user_id 未指定: email で検索
    u = db.query(User).filter(User.email == email).first()
    if not u:
        u = User(name=name, email=email, role="student")
        if avatar is not None and hasattr(u, "avatar"):
            u.avatar = avatar
        db.add(u); db.commit(); db.refresh(u)
        return u

    # 既存ユーザーは display 情報のみ更新（role は維持）
    changed = False
    if name and u.name != name:
        u.name = name; changed = True
    if avatar is not None and hasattr(u, "avatar") and u.avatar != avatar:
        u.avatar = avatar; changed = True
    if changed:
        db.commit(); db.refresh(u)
    return u


def _resolve_user_from_cookie(request: Request, db: Session) -> User | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token or not isinstance(token, str) or not token.startswith("USER:"):
        return None

    try:
        user_id = int(token.split(":", 1)[1])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # 万一消えていたら最低限リカバリ（display 未知）
        user = _ensure_user_exists(db, user_id=user_id, name="User", email=f"user{user_id}@local")
    return user


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """
    /auth/firebase-login で発行した「USER:{id}」型のセッションクッキーのみを受け付ける。
    ダミー運用は完全撤去。
    """
    user = _resolve_user_from_cookie(request, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> User | None:
    """セッションが無ければ None を返す。"""
    try:
        return _resolve_user_from_cookie(request, db)
    except HTTPException:
        # 不正なトークンは 401 をそのまま伝搬
        raise


# --- 管理者判定・ガード ---

def is_admin(user: User) -> bool:
    """role が 'admin' なら管理者。環境変数 ADMIN_EMAILS も許可。"""
    if getattr(user, "role", "") == "admin":
        return True
    allow = os.getenv("ADMIN_EMAILS", "")
    if allow:
        allowed = {e.strip().lower() for e in allow.split(",") if e.strip()}
        if user.email and user.email.lower() in allowed:
            return True
    return False


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """管理者のみ通す依存関数。"""
    if not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return current_user
