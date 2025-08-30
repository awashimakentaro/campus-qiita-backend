# app/schemas/article.py
#schemasフォルダはapiの出入力の方定義をまとめる場所。apiの約束事をまとめているファイル。
#pydantic(fastapiが使うライブラリ)を使いどんなデータを受け取ったり返すのかを定義するのがshemasフォルダ


from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class ArticleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)#...は必須を意味する　minはから文字がダメで魔xは120いしょうはだめ
    body_md: str = Field(..., min_length=10, description="Markdown本文")
    is_published: bool = False
    tags: Optional[List[str]] = Field(default=None, description="タグ名の配列（任意）")
    #これがあることでバリデーション（入力チェック）を自動化　例えばtitleがなかったりすれば422エラーが返ってくるみたい


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    body_md: Optional[str] = Field(default=None, min_length=10)
    is_published: Optional[bool] = None
    tags: Optional[List[str]] = None


class ArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    author_id: int
    title: str
    body_md: str
    body_html: str
    is_published: bool
    likes_count: int = 0
    views: int = 0
    created_at: datetime
    updated_at: datetime
    tags: List[str] = []  # レスポンスはタグ名の配列で返す想定