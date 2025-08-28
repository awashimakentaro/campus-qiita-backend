from fastapi import FastAPI
from app.routers import auth

app = FastAPI(title="UniQiita API", version="0.1.0")

# ルーター登録（/auth/login, /auth/callback など）
app.include_router(auth.router)

# 動作確認用
@app.get("/healthz")
def healthz():
    return {"ok": True}
