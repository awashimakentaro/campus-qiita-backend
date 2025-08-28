from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, func, Index
from . import Base

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    author_id  = Column(Integer, ForeignKey("users.id",    ondelete="CASCADE"), nullable=False)

    body_md   = Column(Text, nullable=False)
    body_html = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_comments_article_id", "article_id"),
        Index("ix_comments_author_id", "author_id"),
    )
