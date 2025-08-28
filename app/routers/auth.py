from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from starlette.requests import Request
import httpx
import os #環境変数を読む
import jwt#ログイン生移行したら自分のサービス用トークンを発行する

router = APIRouter(prefix="/auth", tags=["auth"]) #aut/で始まるurlをここにまとめる

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
ALLOWED_DOMAIN = os.getenv("ALLOWED_DOMAIN")
JWT_SECRET = os.getenv("JWT_SECRET")  # ← ハードコードを削除してenvから読む

# Google の認証ページにリダイレクト
@router.get("/login")#auth/loginってことだね　これはページではなくAPIエンドポイントhttp://localhost:8000/auth/login にアクセスすると、この関数が実行される。
def login():
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"#Googleのログイン画面にアクセスするための固定URL。
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"#ここで.envで指定したリダイレクトurlに飛ぶ
        "&response_type=code"
        "&scope=openid%20email%20profile"
    )
    return RedirectResponse(google_auth_url) #これを返すことで、ブラウザは自動的に Googleのログインページに飛ぶ。

# Google からのコールバックを受け取る
@router.get("/callback")
async def callback(request: Request, code: str):
    token_url = "https://oauth2.googleapis.com/token"

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            token_url,
            data={
                "code": code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        token_data = token_resp.json()

        # IDトークンを取得
        id_token = token_data.get("id_token")
        if not id_token:
            raise HTTPException(status_code=400, detail="Failed to get ID token")

        # JWTをデコード
        payload = jwt.decode(id_token, options={"verify_signature": False})
        email = payload.get("email")

        # ドメインチェック
        if not email.endswith(f"@{ALLOWED_DOMAIN}"): #ここでu-aizu.ac.jpを判別
            raise HTTPException(status_code=403, detail="Domain not allowed")

        # 自前のJWT発行（ユーザー管理につなげる）
        custom_token = jwt.encode({"sub": email}, JWT_SECRET, algorithm="HS256")

        return {"access_token": custom_token, "email": email}
#@router.get("/callback")
#async def callback(request: Request, code: str):
#    # ① Googleに "code" を送ってアクセストークンを取得
#    # ② 返ってきた IDトークン をデコードしてユーザー情報（emailなど）を取り出す
#    # ③ 許可されたドメインかチェック
#    # ④ OKなら自分のJWTを発行して返す
