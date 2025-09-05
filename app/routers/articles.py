# app/routers/articles.p
from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import insert
from pydantic import BaseModel, Field

from app.database import get_db
from app.dependencies import get_current_user
from app.utils.markdown import render_and_sanitize

# モデル
from src.models.article import Article
from src.models.tag import Tag
from src.models.article_tag import article_tags
from src.models.comment import Comment as CommentModel
from src.models.user import User as UserModel

# スキーマ
from app.schemas.article import ArticleCreate, ArticleUpdate, ArticleOut
from app.schemas.article_tag import ArticleTagAttach

# 🔹 ここで router を一度だけ定義（これより上で @router.* は使わない）
router = APIRouter(prefix="/v1/articles", tags=["articles"])

# ====== 記事 CRUD ======
@router.post("/", response_model=ArticleOut)
def create_article(
    article_in: ArticleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    article = Article(
        author_id=current_user.id,
        title=article_in.title,
        body_md=article_in.body_md,
        body_html=render_and_sanitize(article_in.body_md),
        is_published=article_in.is_published,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article

@router.get("/", response_model=List[ArticleOut])
def list_articles(
    query: str | None = Query(None, description="キーワード全文検索"),
    tag: str | None = Query(None, description="タグ名による絞り込み"),
    db: Session = Depends(get_db),
):
    q = db.query(Article).filter(Article.is_published == True)
    if query:
        q = q.filter((Article.title.ilike(f"%{query}%")) | (Article.body_md.ilike(f"%{query}%")))
    if tag:
        q = q.join(article_tags).join(Tag).filter(Tag.name == tag)
    return q.all()
    
@router.get("/me", response_model=List[ArticleOut])
def list_my_articles(
    is_published: bool | None = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    q = db.query(Article).filter(Article.author_id == current_user.id)
    if is_published is not None:
        q = q.filter(Article.is_published == is_published)
    return q.order_by(Article.created_at.desc()).all()  

@router.get("/{article_id}", response_model=ArticleOut)
def get_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if not article.is_published and article.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    return article

@router.patch("/{article_id}", response_model=ArticleOut)
def update_article(
    article_id: int,
    article_in: ArticleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if article.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if article_in.title is not None:
        article.title = article_in.title
    if article_in.body_md is not None:
        article.body_md = article_in.body_md
        article.body_html = render_and_sanitize(article_in.body_md)
    if article_in.is_published is not None:
        article.is_published = article_in.is_published

    db.commit()
    db.refresh(article)
    return article

@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if article.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    db.delete(article)
    db.commit()
    return None

@router.post("/{article_id}/tags", status_code=status.HTTP_204_NO_CONTENT)
def attach_tag_to_article(
    article_id: int,
    payload: ArticleTagAttach,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if article.author_id != current_user.id:
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

# ====== コメント ======
class CommentCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=5000)

class UserOutMini(BaseModel):
    id: str
    name: str
    email: str | None = None
    avatar: str | None = None

class CommentOut(BaseModel):
    id: str
    body: str
    author: UserOutMini
    article_id: str
    createdAt: str
    updatedAt: str

def _to_iso(dt: datetime | None) -> str:
    return (dt or datetime.utcnow()).isoformat()

# これまでの _comment_to_out を差し替え
def _comment_to_out(c: CommentModel, db: Session) -> CommentOut:
    # リレーションがある場合は使い、ない場合は author_id から取得
    author: UserModel | None = getattr(c, "author", None)
    if author is None:
        author_id = getattr(c, "author_id", None)
        if author_id is not None:
            author = db.query(UserModel).filter(UserModel.id == author_id).first()

    # フォールバック（authorが取得できない場合の最低限）
    author_out = UserOutMini(
        id=str(getattr(author, "id", "")),
        name=getattr(author, "name", "Unknown"),
        email=getattr(author, "email", None),
        avatar=getattr(author, "avatar", None),
    )

    return CommentOut(
        id=str(c.id),
        body=getattr(c, "body_md", None) or getattr(c, "body", "") or "",
        author=author_out,
        article_id=str(c.article_id),
        createdAt=_to_iso(getattr(c, "created_at", None)),
        updatedAt=_to_iso(getattr(c, "updated_at", None)),
    )
# ====== コメント ======

@router.get("/{article_id}/comments", response_model=List[CommentOut])
def list_comments(
    article_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    comments = (
        db.query(CommentModel)
        .filter(CommentModel.article_id == article_id)
        .order_by(CommentModel.created_at.asc())
        .all()
    )
    return [_comment_to_out(c, db) for c in comments]  # ← db を渡す


@router.post("/{article_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(
    article_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # 記事の存在チェック
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    body_md = (payload.body or "").strip()
    if not body_md:
        raise HTTPException(status_code=422, detail="body is required")

    # Markdown→HTML（存在すれば使う）
    body_html = render_and_sanitize(body_md)

    # ✅ ここで fields を定義してから CommentModel に渡す
    fields = {"article_id": article_id, "author_id": current_user.id}
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

    # _comment_to_out は db を渡す新版を使うこと（前の手順で差し替え済みのはず）
    return _comment_to_out(c, db)

# 自分の記事一覧（公開/非公開どちらも。is_published を付ければ絞り込み可）
