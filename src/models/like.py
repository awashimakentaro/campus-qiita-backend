from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint, func, Index
from . import Base

class Like(Base):
    __tablename__ = "likes"

    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("article_id", "user_id", name="uq_like_article_user"),
        Index("ix_likes_article_id", "article_id"),
        Index("ix_likes_user_id", "user_id"),
    )
