
#routerにファイルを書き込むとswaggerに表示される
# app/routers/articles.py
from fastapi import APIRouter

router = APIRouter(prefix="/v1/articles", tags=["articles"])

@router.get("/ping")
def ping():
    # まずは疎通確認だけ
    return {"ok": True, "where": "/v1/articles/ping"}