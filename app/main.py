from fastapi import FastAPI
from app.routers import auth
from fastapi.middleware.cors import CORSMiddleware
from app.routers.articles import router as articles_router

app = FastAPI(title="UniQiita API", version="0.1.0")
#なんこれ
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ルーター登録（/auth/login, /auth/callback など）
app.include_router(auth.router)
app.include_router(articles_router)

# 動作確認用
@app.get("/healthz")
def healthz():
    return {"ok": True}
