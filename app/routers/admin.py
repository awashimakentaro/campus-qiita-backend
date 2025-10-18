# app/routers/admin.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from src.models.user import User as UserModel
from src.models.article import Article
from src.models.comment import Comment
from src.models.like import Like
from src.models.article_tag import article_tags

router = APIRouter(prefix="/v1/admin", tags=["admin"], redirect_slashes=False)

def _purge_user_data(db: Session, user_id: int) -> int:
    """
    指定ユーザーが関わるデータを削除。
    - いいね
    - コメント
    - 記事（記事に紐づく中間テーブルも先に削除）
    戻り値: 削除した記事数（目安用）
    """
    # いいね（自分が付けたもの）
    db.query(Like).filter(Like.user_id == user_id).delete(synchronize_session=False)
    # コメント（自分が書いたもの）
    db.query(Comment).filter(Comment.author_id == user_id).delete(synchronize_session=False)

    # 自分の記事に紐づく中間テーブル（article_tags, likes, comments）を先に削除
    my_articles = db.query(Article).filter(Article.author_id == user_id).all()
    article_ids = [a.id for a in my_articles]
    if article_ids:
        db.execute(article_tags.delete().where(article_tags.c.article_id.in_(article_ids)))
        db.query(Like).filter(Like.article_id.in_(article_ids)).delete(synchronize_session=False)
        db.query(Comment).filter(Comment.article_id.in_(article_ids)).delete(synchronize_session=False)
        db.query(Article).filter(Article.id.in_(article_ids)).delete(synchronize_session=False)

    db.commit()
    return len(article_ids)


@router.delete("/purge/by-email", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/purge/by-email/", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def purge_by_email(
    email: str = Query(..., description="削除対象ユーザーのメールアドレス"),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """管理者専用: 指定メールアドレスのユーザーの投稿/コメント/いいねを全削除。"""
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 自分自身のデータも削除可能だが、誤操作防止で警告したい場合はここでブロック可
    _purge_user_data(db, user.id)
    return None


@router.delete("/purge/dummy", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/purge/dummy/", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def purge_dummy(
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """
    管理者専用: 典型的なダミー条件で一括削除。
    必要に応じて条件を調整（例: name='Dummy' など）。
    """
    targets = db.query(UserModel).filter(UserModel.email.like("dummy%@%")).all()
    for u in targets:
        _purge_user_data(db, u.id)
    return None
