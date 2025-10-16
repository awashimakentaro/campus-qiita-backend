from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from app.routers import auth
from fastapi.middleware.cors import CORSMiddleware
from app.routers.articles import router as articles_router
from app.routers import tags
from app.routers import admin

app = FastAPI(title="UniQiita API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(auth.router)
app.include_router(articles_router)
app.include_router(tags.router)
app.include_router(admin.router)

# ✅ /healthz を GET/HEAD 両対応に
@app.api_route("/healthz", methods=["GET", "HEAD"])
def healthz():
    # HEAD のときはボディは無視されるが、返してもOK
    return PlainTextResponse("ok", status_code=200)
