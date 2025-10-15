# app/routers/articles.py
from __future__ import annotations

from typing import List, Literal, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, insert

from app.database import get_db
from app.dependencies import get_current_user, is_admin
from app.utils.markdown import render_and_sanitize

# --- Models ---
from src.models.article import Article
from src.models.user import User as UserModel
from src.models.tag import Tag
from src.models.article_tag import article_tags
from src.models.comment import Comment as CommentModel
from src.models.like import Like

# スラ自動リダイレクト(307)を無効化
router = APIRouter(
    prefix="/v1/articles",
    tags=["articles"],
    redirect_slashes=False,
)

# ======================================================
# 共通: シリアライザ
# ======================================================

def _serialize_user(u: Optional[UserModel]) -> Optional[dict]:
    if not u:
        return None
    return {"id": u.id, "name": u.name, "email": u.email, "avatar": getattr(u, "avatar", None)}

def _serialize_article(a: Article, likes_count: Optional[int] = None, comments_count: Optional[int] = None) -> dict:
    return {
        "id": a.id,
        "author_id": a.author_id,
        "title": a.title,
        "body_md": a.body_md,
        "body_html": a.body_html,
        "is_published": a.is_published,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        "likes_count": int(likes_count if likes_count is not None else getattr(a, "likes_count", 0) or 0),
        "comments_count": int(comments_count if comments_count is not None else getattr(a, "comments_count", 0) or 0),
        "author": _serialize_user(getattr(a, "author", None)),
        # タグを返したい場合は以下を有効化（Tag リレーションを設定している前提）
        # "tags": [{"id": t.id, "name": t.name} for t in getattr(a, "tags", [])],
    }

def _iso(dt: datetime | None) -> str:
    return (dt or datetime.utcnow()).isoformat()

def _serialize_comment(c: CommentModel, db: Session) -> dict:
    # リレーションが無い場合は author_id から取得
    author: UserModel | None = getattr(c, "author", None)
    if author is None and hasattr(c, "author_id"):
        author = db.query(UserModel).filter(UserModel.id == c.author_id).first()

    # 本文は body_md 優先、無ければ body
    body_text = getattr(c, "body_md", None) or getattr(c, "body", "") or ""

    return {
        "id": getattr(c, "id", ""),
        "body": body_text,
        "author": _serialize_user(author),
        "article_id": getattr(c, "article_id", ""),
        "createdAt": _iso(getattr(c, "created_at", None)),
        "updatedAt": _iso(getattr(c, "updated_at", None)),
    }

def _count_likes(db: Session, article_id: int) -> int:
    return (db.query(func.count(Like.user_id)).filter(Like.article_id == article_id).scalar() or 0)

# =======================
# 記事: 作成
# =======================

@router.post("/", response_model=dict)
def create_article(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    title = (data or {}).get("title")
    body_md = (data or {}).get("body_md")
    if not title or not body_md:
        raise HTTPException(status_code=400, detail="Missing required fields")

    body_html = (data or {}).get("body_html") or render_and_sanitize(body_md)
    is_published = bool((data or {}).get("is_published", False))

    article = Article(
        author_id=current_user.id,
        title=title,
        body_md=body_md,
        body_html=body_html,
        is_published=is_published,
    )
    db.add(article)
    db.commit()

    a = db.query(Article).options(joinedload(Article.author)).filter(Article.id == article.id).first()
    return _serialize_article(a or article)

# スラ無しでも作成OK（スキーマ非表示）
@router.post("", response_model=dict, include_in_schema=False)
def create_article_no_slash(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    return create_article(data=data, db=db, current_user=current_user)

# =======================
# 記事: 一覧
# =======================

@router.get("/", response_model=List[dict])
def list_articles(
    query: str | None = Query(None, description="キーワード全文検索"),
    tag: str | None = Query(None, description="タグ名で絞り込み"),
    sort: Literal["popular", "recent", "comments"] = Query("popular", description="並び替え"),
    db: Session = Depends(get_db),
):
    # いいね数 / コメント数のサブクエリ
    likes_sq = (
        db.query(Like.article_id.label("article_id"), func.count(Like.user_id).label("likes_count"))
        .group_by(Like.article_id)
        .subquery()
    )
    comments_sq = (
        db.query(CommentModel.article_id.label("article_id"), func.count(CommentModel.id).label("comments_count"))
        .group_by(CommentModel.article_id)
        .subquery()
    )

    # 公開記事のみ + author を eager load
    q = (
        db.query(
            Article,
            func.coalesce(likes_sq.c.likes_count, 0).label("likes_count"),
            func.coalesce(comments_sq.c.comments_count, 0).label("comments_count"),
        )
        .outerjoin(likes_sq, likes_sq.c.article_id == Article.id)
        .outerjoin(comments_sq, comments_sq.c.article_id == Article.id)
        .options(joinedload(Article.author))
        .filter(Article.is_published == True)  # noqa: E712
    )

    if query:
        like = f"%{query}%"
        q = q.filter((Article.title.ilike(like)) | (Article.body_md.ilike(like)))

    if tag:
        q = (
            q.join(article_tags, article_tags.c.article_id == Article.id)
             .join(Tag, Tag.id == article_tags.c.tag_id)
             .filter(Tag.name == tag)
        )

    if sort == "popular":
        q = q.order_by(func.coalesce(likes_sq.c.likes_count, 0).desc(), Article.created_at.desc())
    elif sort == "comments":
        q = q.order_by(func.coalesce(comments_sq.c.comments_count, 0).desc(), Article.created_at.desc())
    else:
        q = q.order_by(Article.created_at.desc())

    rows = q.all()
    return [_serialize_article(a, likes_count, comments_count) for a, likes_count, comments_count in rows]

# スラ無しでも一覧OK（スキーマ非表示）
@router.get("", response_model=List[dict], include_in_schema=False)
def list_articles_no_slash(
    query: str | None = Query(None),
    tag: List[str] | None = Query(None),
    sort: Literal["popular", "recent", "comments"] = Query("popular"),
    db: Session = Depends(get_db),
):
    return list_articles(query=query, tag=tag, sort=sort, db=db)

# =======================
# 記事: 自分の投稿
# =======================

@router.get("/me", response_model=List[dict])
def list_my_articles(
    is_published: bool | None = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    q = db.query(Article).options(joinedload(Article.author)).filter(Article.author_id == current_user.id)
    if is_published is not None:
        q = q.filter(Article.is_published == is_published)
    rows = q.order_by(Article.created_at.desc()).all()

    out: List[dict] = []
    for a in rows:
        likes = _count_likes(db, a.id)
        comments = (db.query(func.count(CommentModel.id)).filter(CommentModel.article_id == a.id).scalar() or 0)
        out.append(_serialize_article(a, likes, comments))
    return out

# =======================
# 記事: 取得
# =======================

@router.get("/{article_id}", response_model=dict)
def get_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    a = db.query(Article).options(joinedload(Article.author)).filter(Article.id == article_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Article not found")
    if not a.is_published and a.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    likes = _count_likes(db, article_id)
    comments = (db.query(func.count(CommentModel.id)).filter(CommentModel.article_id == article_id).scalar() or 0)
    return _serialize_article(a, likes, comments)

# =======================
# 記事: 更新 / 削除
# =======================

@router.patch("/{article_id}", response_model=dict)
def update_article(
    article_id: int,
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    a = db.query(Article).filter(Article.id == article_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Article not found")
    if a.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    title = (data or {}).get("title")
    body_md = (data or {}).get("body_md")
    is_published = (data or {}).get("is_published")

    if title is not None:
        a.title = title
    if body_md is not None:
        a.body_md = body_md
        a.body_html = render_and_sanitize(body_md)
    if is_published is not None:
        a.is_published = bool(is_published)

    db.commit()

    a = db.query(Article).options(joinedload(Article.author)).filter(Article.id == article_id).first()
    likes = _count_likes(db, article_id)
    comments = (db.query(func.count(CommentModel.id)).filter(CommentModel.article_id == article_id).scalar() or 0)
    return _serialize_article(a, likes, comments)

@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if article.author_id != current_user.id and not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Not allowed")
    db.delete(article)
    db.commit()
    return None

# =======================
# タグ付け / コメント / いいね
# =======================

from app.schemas.article_tag import ArticleTagAttach
from pydantic import BaseModel, Field

@router.post("/{article_id}/tags", status_code=status.HTTP_204_NO_CONTENT)
def attach_tag_to_article(
    article_id: int,
    payload: ArticleTagAttach,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    a = db.query(Article).filter(Article.id == article_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Article not found")
    if a.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    tag = db.query(Tag).filter(Tag.id == payload.tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    try:
        db.execute(insert(article_tags).values(article_id=article_id, tag_id=payload.tag_id))
        db.commit()
    except Exception:
        db.rollback()
    return None

class CommentCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=5000)

@router.get("/{article_id}/comments", response_model=List[dict])
def list_comments(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    comments = (
        db.query(CommentModel)
        .filter(CommentModel.article_id == article_id)
        .order_by(CommentModel.created_at.asc())
        .all()
    )
    return [_serialize_comment(c, db) for c in comments]

@router.post("/{article_id}/comments", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_comment(
    article_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    body_md = (payload.body or "").strip()
    if not body_md:
        raise HTTPException(status_code=422, detail="body is required")

    body_html = render_and_sanitize(body_md)

    fields: dict = {"article_id": article_id, "author_id": current_user.id}
    if hasattr(CommentModel, "body_md"):
        fields["body_md"] = body_md
        if hasattr(CommentModel, "body_html"):
            fields["body_html"] = body_html
    elif hasattr(CommentModel, "body"):
        fields["body"] = body_md
        if hasattr(CommentModel, "body_html"):
            fields["body_html"] = body_html
    else:
        raise HTTPException(status_code=500, detail="Comment model has no body/body_md column")

    c = CommentModel(**fields)
    db.add(c)
    db.commit()
    db.refresh(c)
    return _serialize_comment(c, db)

@router.get("/{article_id}/likes", response_model=dict)
def get_like_status(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    a = db.query(Article).filter(Article.id == article_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Article not found")
    liked = (db.query(Like).filter(Like.article_id == article_id, Like.user_id == current_user.id).first() is not None)
    return {"liked": liked, "likes_count": _count_likes(db, article_id)}

@router.post("/{article_id}/likes", response_model=dict, status_code=status.HTTP_201_CREATED)
def like_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    a = db.query(Article).filter(Article.id == article_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Article not found")

    exists = db.query(Like).filter(Like.article_id == article_id, Like.user_id == current_user.id).first()
    if not exists:
        db.add(Like(article_id=article_id, user_id=current_user.id))
        db.commit()
    return {"liked": True, "likes_count": _count_likes(db, article_id)}

@router.delete("/{article_id}/likes", response_model=dict)
def unlike_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    a = db.query(Article).filter(Article.id == article_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Article not found")

    like = db.query(Like).filter(Like.article_id == article_id, Like.user_id == current_user.id).first()
    if like:
        db.delete(like)
        db.commit()
    return {"liked": False, "likes_count": _count_likes(db, article_id)}

@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if article.author_id != current_user.id and not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Not allowed")
    db.delete(article)
    db.commit()
    return None
