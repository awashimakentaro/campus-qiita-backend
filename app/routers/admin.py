# app/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from src.models.user import User
from src.models.article import Article
from src.models.comment import Comment
from src.models.like import Like
from src.models.article_tag import article_tags

router = APIRouter(prefix="/admin", tags=["admin"])

def is_admin(user: User) -> bool:
    return getattr(user, "role", "") == "admin"

# 🔹 全記事削除（管理者専用）
@router.delete("/articles", status_code=204)
def delete_all_articles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Not allowed")

    # 関連するコメント・いいね・タグ付けも消す
    db.query(Comment).delete()
    db.query(Like).delete()
    db.execute(article_tags.delete())
    db.query(Article).delete()
    db.commit()
    return None

# 🔹 全コメント削除（管理者専用）
@router.delete("/comments", status_code=204)
def delete_all_comments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Not allowed")

    db.query(Comment).delete()
    db.commit()
    return None