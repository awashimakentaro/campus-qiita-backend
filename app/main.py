# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, tags, admin
from app.routers.articles import router as articles_router

app = FastAPI(title="UniQiita API", version="0.1.0")

# ---- CORS 設定 ----
# Railway の Variables に CORS_ALLOW_ORIGINS を入れておくと本番で使われます。
# 例: "https://<your-vercel>.vercel.app, http://localhost:3000, http://127.0.0.1:3000"
raw = os.getenv("CORS_ALLOW_ORIGINS", "")
if raw.strip():
    ALLOW_ORIGINS = [o.strip() for o in raw.split(",") if o.strip()]
else:
    # ローカル用デフォルト（本番は上の環境変数で上書き）
    ALLOW_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=True,  # Cookie 認証するなら必須
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ---- ルーター ----
app.include_router(auth.router)
app.include_router(articles_router)
app.include_router(tags.router)
app.include_router(admin.router)

# ---- ヘルスチェック ----
@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"ok": True}