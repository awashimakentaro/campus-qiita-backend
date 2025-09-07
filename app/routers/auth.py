# app/routers/auth.py
import os
import urllib.parse
import secrets
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session

# 既存依存
from app.database import get_db
from app.dependencies import get_current_user
from src.models.user import User as UserModel

# Firebase 管理 SDK（初期化は app/core/firebase.py 側で実施している想定）
try:
    from firebase_admin import auth as firebase_auth  # type: ignore
    from app.core.firebase import *  # noqa: F401 (初期化が副作用で行われる想定)
    _FIREBASE_AVAILABLE = True
except Exception:
    _FIREBASE_AVAILABLE = False

router = APIRouter(prefix="/auth", tags=["auth"])

# ====== 設定・定数 ======
GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")

FRONTEND_BASE = os.getenv("FRONTEND_BASE", "http://localhost:3000")
SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "session")  # FEからは読み取れないHttpOnly Cookie
POST_LOGIN_COOKIE = "post_login_redirect"  # ログイン後に戻す先を一時保存

# ------------------------------------------------------------
# 既存: Google OAuth（ダミー運用）
# ------------------------------------------------------------

# GET /auth/login?redirect=/articles/new
@router.get("/login")
def start_google_login(redirect: Optional[str] = None):
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID not set")

    state = secrets.token_urlsafe(16)
    scopes = [
        "openid",
        "email",
        "profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "online",
        "include_granted_scopes": "true",
        "state": state,
    }
    url = f"{GOOGLE_AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}"

    resp = RedirectResponse(url, status_code=302)
    # ローカル開発: secure=False / SameSite=Lax
    resp.set_cookie(
        key=POST_LOGIN_COOKIE,
        value=(redirect or f"{FRONTEND_BASE}/"),
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 10,  # 10分
        path="/",
    )
    resp.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 10,
        path="/",
    )
    return resp


# GET /auth/callback
@router.get("/callback")
async def oauth_callback(request: Request, code: Optional[str] = None, state: Optional[str] = None):
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    # TODO: state 照合, code→token 交換, userinfo 取得, DB upsert, 自前JWT発行
    # まずはダミー運用
    jwt_token = "DUMMY_JWT_FOR_LOCAL"

    redirect_to = request.cookies.get(POST_LOGIN_COOKIE) or FRONTEND_BASE
    resp = RedirectResponse(url=redirect_to, status_code=302)
    resp.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=jwt_token,
        httponly=True,
        secure=False,   # 本番(https)では True
        samesite="lax", # 本番クロスサイト要件次第で "none"(secure必須) も検討
        max_age=60 * 60 * 24 * 7,  # 7日
        path="/",
    )
    resp.delete_cookie(POST_LOGIN_COOKIE, path="/")
    resp.delete_cookie("oauth_state", path="/")
    return resp


# ------------------------------------------------------------
# 新規: Firebase ログイン（ID トークン検証）
# ------------------------------------------------------------

@router.post("/firebase-login")
async def firebase_login(request: Request, db: Session = Depends(get_db)):
    """
    フロントから { idToken } を受け取り、Firebase で検証。
    DBにユーザーを作成/更新し、セッションクッキーを発行して 200 を返す。
    レスポンスボディにはユーザー情報を返す。
    """
    if not _FIREBASE_AVAILABLE:
        raise HTTPException(status_code=500, detail="Firebase Admin SDK is not available")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    id_token = body.get("idToken")
    if not id_token:
        raise HTTPException(status_code=400, detail="idToken is required")

    try:
        decoded = firebase_auth.verify_id_token(id_token, clock_skew_seconds=60)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid ID token: {str(e)}")
    # Firebase payload から情報抽出

    uid = decoded.get("uid")
    email = decoded.get("email")
    name = decoded.get("name") or "Unknown"
    picture = decoded.get("picture")

    if not email:
        # email 非提供のプロバイダもあるが、その場合は別の識別子運用が必要
        raise HTTPException(status_code=400, detail="Email not provided by identity provider")

        # DB upsert
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        # モデルに存在するフィールドだけ安全にセット
        user = UserModel(name=name, email=email)
        # avatar カラムがある環境だけ反映（無ければスキップ）
        if hasattr(UserModel, "avatar"):
            setattr(user, "avatar", picture)
        db.add(user)
    else:
        user.name = name
        if hasattr(UserModel, "avatar"):
            setattr(user, "avatar", picture)

    db.commit()
    db.refresh(user)

    # 既存の仕組みに寄せ、簡易セッションクッキー（USER:{id}）を発行
    # ※ get_current_user 側で USER:xxx を許容する実装が必要になります
    session_value = f"USER:{user.id}"
    resp = JSONResponse(
    status_code=200,
    content={
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "avatar": getattr(user, "avatar", None),  # ← ここを安全に
    },
)
    resp.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_value,
        httponly=True,
        secure=False,   # 本番(https)では True
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7日
        path="/",
    )
    return resp


# ------------------------------------------------------------
# ログアウト（クッキー削除）
# ------------------------------------------------------------

@router.post("/logout")
def logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return resp


# ------------------------------------------------------------
# 現ユーザー
# ------------------------------------------------------------

@router.get("/me")
def get_me(user: UserModel = Depends(get_current_user)):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "avatar": getattr(user, "avatar", None),
        "role": getattr(user, "role", "student"),
    }