# app/routers/auth.py
import os
import urllib.parse
import secrets
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# ====== 設定・定数 ======
GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")

FRONTEND_BASE = os.getenv("FRONTEND_BASE", "http://localhost:3000")
SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "session")  # FEからは読み取れないHttpOnly Cookie
POST_LOGIN_COOKIE = "post_login_redirect"  # ログイン後に戻す先を一時保存

# ====== /auth/login: Google 認可画面へリダイレクト ======
# 例: GET /auth/login?redirect=/articles/new
@router.get("/login")
def start_google_login(redirect: str | None = None):
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID not set")

    # CSRF対策のstate（最小限の例。実運用はサーバー側ストア等で照合を）
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
        # "prompt": "consent",  # 毎回同意を出したい場合のみ
    }
    url = f"{GOOGLE_AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}"

    # 302でGoogleへ
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


# ====== /auth/callback: Google から戻る場所 ======
# ここで code→Googleトークン交換→ユーザー情報取得→自前JWT発行→Cookieにセット→FEへ302
@router.get("/callback")
async def oauth_callback(request: Request, code: str | None = None, state: str | None = None):
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    # TODO: ここで 'state' の照合を行う（Cookie or サーバー側ストアの値と一致するか）
    # state_cookie = request.cookies.get("oauth_state")

    # TODO: ここで 'code' を使って Google のトークンに交換し、userinfo を取得する
    # 例:
    # token = await exchange_code_for_token(code, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI)
    # userinfo = await fetch_google_userinfo(token["access_token"])
    # そして学内ドメイン（@u-aizu.ac.jp 等）チェック → 自前JWT作成

    # まずはローカル動作確認用のダミーJWTを使用（後で上の実装に差し替え）
    jwt_token = "DUMMY_JWT_FOR_LOCAL"

    # 戻り先URL（/auth/login でCookieに入れた値を優先）
    redirect_to = request.cookies.get(POST_LOGIN_COOKIE) or FRONTEND_BASE

    # FEへ302しつつ、セッションクッキーをセット
    resp = RedirectResponse(url=redirect_to, status_code=302)
    resp.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=jwt_token,
        httponly=True,
        secure=False,   # 本番(https)では True
        samesite="lax", # 本番でクロスサイトPOST等が必要なら "none" を検討（secure=True必須）
        max_age=60 * 60 * 24 * 7,  # 7日
        path="/",
    )

    # 一度きりのCookieは削除
    resp.delete_cookie(POST_LOGIN_COOKIE, path="/")
    resp.delete_cookie("oauth_state", path="/")
    return resp

# app/routers/auth.py（末尾に追加）
from fastapi import Depends
from sqlalchemy.orm import Session
from app.dependencies import get_current_user  # ← あなたのパスに合わせて
from src.models.user import User  # ← モデルのパスに合わせて

@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    # フロントで必要な最小のプロパティを返す
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": getattr(user, "role", "student"),
    }