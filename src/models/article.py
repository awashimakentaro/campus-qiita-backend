from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from . import Base

class Article(Base):
    __tablename__ = "articles"#これはarticleclassをarticleテーブルとして扱う宣言

    id = Column(Integer, primary_key=True)
    #primary keyとはusersなら、このレコードはユーザー42だと特定するためのもの。integerとあるがUUID（重複しづらいランダムID
    #primary_key=Trueとはそのカラムを主キーにするという宣言　postgressqlが自動採番してくれる
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    #ForeignKeとすることでauthor_id = ser.id　のような連携ができる
    title = Column(String(200), nullable=False)       # 記事タイトル
    body_md = Column(Text, nullable=False)            # Markdownの原文（投稿/編集の元データ）
    body_html = Column(Text, nullable=False)          # サーバー側でサニタイズして保存する描画用HTML
    is_published = Column(Boolean, nullable=False, default=False)  # 下書き/公開フラグ

    score = Column(Integer, nullable=False, default=0)  # 人気順スコア（簡易キャッシュ）
    views = Column(Integer, nullable=False, default=0)  # 閲覧数（将来の集計用）

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # リレーション（後でUser側にも対応を追加する）
    author = relationship("User", back_populates="articles")
    #「記事 ↔ 作者」をオブジェクトで行き来できる近道　自動同期できる。片側を触れば両側が揃う（back_populates の効果）。