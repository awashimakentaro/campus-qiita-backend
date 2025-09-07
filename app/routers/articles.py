# app/routers/articles.py
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from src.models.article import Article
from src.models.user import User

router = APIRouter(prefix="/v1/articles", tags=["articles"])


# --------- serializers ---------
def serialize_user(u: Optional[User]) -> Optional[dict]:
    if not u:
        return None
    return {
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "avatar": getattr(u, "avatar", None),
    }


def serialize_article(a: Article) -> dict:
    likes_count = getattr(a, "likes_count", None)
    comments_count = getattr(a, "comments_count", None)
    return {
        "id": a.id,
        "author_id": a.author_id,
        "title": a.title,
        "body_md": a.body_md,
        "body_html": a.body_html,
        "is_published": a.is_published,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        "likes_count": likes_count if isinstance(likes_count, int) else 0,
        "comments_count": comments_count if isinstance(comments_count, int) else 0,
        "author": serialize_user(a.author),
        # "tags": [{"id": t.id, "name": t.name} for t in getattr(a, "tags", [])],
    }


# --------- list / retrieve ---------
@router.get("", response_model=List[dict])
def list_articles(
    db: Session = Depends(get_db),
    query: Optional[str] = Query(None),
    tag: Optional[List[str]] = Query(None),
    is_published: Optional[bool] = Query(True),
    sort: Optional[str] = Query("recent"),  # "recent" | "popular"
):
    q = db.query(Article).options(joinedload(Article.author))

    if is_published is not None:
        q = q.filter(Article.is_published == is_published)

    if query:
        like = f"%{query}%"
        q = q.filter((Article.title.ilike(like)) | (Article.body_md.ilike(like)))

    # TODO: タグで絞る場合はここで JOIN + filter

    if sort == "popular":
        q = q.order_by(desc(Article.score), desc(Article.created_at))
    else:
        q = q.order_by(desc(Article.created_at))

    articles = q.all()
    return [serialize_article(a) for a in articles]


@router.get("/{article_id}", response_model=dict)
def get_article(article_id: int, db: Session = Depends(get_db)):
    a = (
        db.query(Article)
        .options(joinedload(Article.author))
        .filter(Article.id == article_id)
        .first()
    )
    if not a:
        raise HTTPException(status_code=404, detail="Article not found")
    return serialize_article(a)


# --------- create ---------
@router.post("", response_model=dict)
@router.post("/", response_model=dict)  # スラッシュあり/なし両対応
def create_article(
    data: Dict[str, Any] = Body(...),         # { title, body_md, is_published? , body_html? }
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # ← クッキーのセッションから
):
    # 必須チェック
    title = (data or {}).get("title")
    body_md = (data or {}).get("body_md")
    if not title or not body_md:
        raise HTTPException(status_code=400, detail="Missing required fields")

    # body_html 未指定ならひとまず body_md をそのまま使う
    # ※ 後で Markdown→HTML + サニタイズに置き換え推奨
    body_html = (data or {}).get("body_html") or body_md

    article = Article(
        author_id=current_user.id,
        title=title,
        body_md=body_md,
        body_html=body_html,
        is_published=bool((data or {}).get("is_published", False)),
    )
    db.add(article)
    db.commit()
    # author を含めて返すために joinedload で再取得（または手動でセット）
    a = (
        db.query(Article)
        .options(joinedload(Article.author))
        .filter(Article.id == article.id)
        .first()
    )
    return serialize_article(a or article)