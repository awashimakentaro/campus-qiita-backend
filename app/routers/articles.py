# app/routers/articles.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.article import ArticleCreate, ArticleUpdate, ArticleOut
from src.models.article import Article
from app.database import get_db
from app.utils.markdown import render_and_sanitize
from app.dependencies import get_current_user  # 認証済ユーザーを取る関数（既存想定）

router = APIRouter(
    prefix="/v1/articles",
    tags=["articles"],
)

# 記事作成
@router.post("/", response_model=ArticleOut)#response_model=ArticleOutはAritcleoutの形で整形して返すという意味dbモデルのままでなく必要なフィールドで抜き出してjそんする
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

# 記事一覧（公開済みのみ）
@router.get("/", response_model=List[ArticleOut])
def list_articles(db: Session = Depends(get_db)):
    return db.query(Article).filter(Article.is_published == True).all()

# 記事詳細（公開済み or 自分の）
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

# 記事更新（本人のみ）
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

# 記事削除（本人のみ）
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