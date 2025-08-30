# app/schemas/article.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# 記事作成用
class ArticleCreate(BaseModel):
    title: str
    body_md: str
    is_published: bool = False   # デフォは下書き

# 記事更新用
class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    body_md: Optional[str] = None
    is_published: Optional[bool] = None

# 出力用（一覧や詳細で返す）
class ArticleOut(BaseModel):
    id: int
    author_id: int
    title: str
    body_md: str
    body_html: str
    is_published: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True