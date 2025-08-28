from sqlalchemy import Column, Integer, String, DateTime, func, UniqueConstraint
from . import Base

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    # タグ名（例: "離散数学", "Python"）
    # uniqueにしたいが、将来大文字小文字/全角半角の正規化を入れる可能性があるため
    # まずはDBレベルでも UNIQUE を掛けておく
    name = Column(String(50), nullable=False, unique=True)

    # 表示や検索の安定化のため、将来 slug（小文字・半角・ハイフン）を追加してもOK
    # slug = Column(String(64), unique=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 追加の複合一意制約を入れたい場合はこの形で増やせる
    __table_args__ = (
        UniqueConstraint("name", name="uq_tags_name"),
    )
