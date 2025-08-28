from sqlalchemy import Table, Column, Integer, ForeignKey, UniqueConstraint, Index
from . import Base

# 多対多の“橋渡しテーブル”
# Article(1) ---< article_tags >--- (1) Tag
article_tags = Table(
    "article_tags",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False),

    # 同じ記事に同じタグを重複して付けられないようにする
    UniqueConstraint("article_id", "tag_id", name="uq_article_tag"),

    # よく検索する組み合わせにインデックスを貼っておく（将来のパフォーマンス用）
    Index("ix_article_tags_article_id", "article_id"),
    Index("ix_article_tags_tag_id", "tag_id"),
)
