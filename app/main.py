# app/main.py
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, tags, admin
from app.routers.articles import router as articles_router

app = FastAPI(title="UniQiita API", version="0.1.0")

# ★ CORS：本番Vercelとプレビューを正規表現で許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://campus-qiita-frontend.vercel.app",  # 本番
    ],
    allow_origin_regex=r"^https://campus-qiita-frontend(-[a-z0-9\-]+)?\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(auth.router)
app.include_router(articles_router)
app.include_router(tags.router)
app.include_router(admin.router)

@app.api_route("/healthz", methods=["GET", "HEAD"])
def healthz():
    return PlainTextResponse("ok", status_code=200)
