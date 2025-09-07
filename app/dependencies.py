# app/dependencies.py
# 依存を注入（DB / 認証ユーザー）。Firebase 未設定でも絶対に落ちない安全版。

import os
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from src.models.user import User  # モデルのパスは既存通り

SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "session")
ENV = os.getenv("ENV", "dev").lower()  # dev / development / local を開発扱いに

def _ensure_user_exists(
    db: Session,
    *,
    user_id: int | None = None,
    name: str,
    email: str,
    avatar: str | None = None,
) -> User:
    """
    指定ユーザーが存在しなければ作る。存在すれば最低限の項目を更新。
    user_id 指定あり: id で検索/作成
    user_id 指定なし: email で検索/作成
    """
    if user_id is not None:
        u = db.query(User).filter(User.id == user_id).first()
        if not u:
            u = User(id=user_id, name=name, email=email, avatar=avatar, role="student")
            db.add(u)
            db.commit()
            db.refresh(u)
            return u
        # 既存を軽く更新（必要なら）
        updated = False
        if name and u.name != name:
            u.name = name
            updated = True
        if avatar is not None and getattr(u, "avatar", None) != avatar:
            u.avatar = avatar
            updated = True
        if updated:
            db.commit()
            db.refresh(u)
        return u

    # user_id なし → email で upsert
    u = db.query(User).filter(User.email == email).first()
    if not u:
        u = User(name=name, email=email, avatar=avatar, role="student")
        db.add(u)
        db.commit()
        db.refresh(u)
    return u


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """
    セッションクッキーを読んでユーザーを返す。
    - "USER:{id}" ならその ID のユーザー（なければ作成）
    - "DUMMY_JWT_FOR_LOCAL" なら id=1 のダミー
    - それ以外/未設定は:
        - 開発環境(dev/development/local) → ダミー(id=1)
        - 本番 → 401
    """
    token = request.cookies.get(SESSION_COOKIE_NAME)

    # 1) Firebase 等で発行した簡易セッション "USER:{id}"
    if isinstance(token, str) and token.startswith("USER:"):
        try:
            user_id = int(token.split(":", 1)[1])
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")

        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return user
        # 万一存在しない場合は最低限で再生成
        return _ensure_user_exists(
            db,
            user_id=user_id,
            name="User",
            email=f"user{user_id}@local",
            avatar=None,
        )

    # 2) 既存ダミー互換
    if token == "DUMMY_JWT_FOR_LOCAL":
        return _ensure_user_exists(
            db,
            user_id=1,
            name="Dummy",
            email="dummy@u-aizu.ac.jp",
            avatar=None,
        )

    # 3) 未設定/未知
    if ENV in ("dev", "development", "local"):
        # 開発はダミーで継続
        return _ensure_user_exists(
            db,
            user_id=1,
            name="Dummy",
            email="dummy@u-aizu.ac.jp",
            avatar=None,
        )

    # 本番は 401
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")