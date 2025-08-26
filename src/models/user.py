from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship 
from . import Base  # 同じパッケージ内の Base を使う

class User(Base):#Python のクラスを使ってusers というテーブルを作り、id, name, email, role, bio, created_at という列を持たせ、制約やデフォルト値も決めている
    __tablename__ = "users" #userクラスがusersテーブルになりますという宣言

    id = Column(Integer, primary_key=True, index=True) #Column … テーブルの列を表す。 primary_key=True … 主キー（重複不可、1レコードを一意に識別）。  index=True … 検索用のインデックスを貼る。検索が速くなる。
    name = Column(String(100), nullable=False) #String(100) → 最大100文字の文字列 nullable=False → 空（NULL）を許さない unique=True → 重複を禁止（email は世界で1つだけ）
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(50), nullable=False, default="student")  # student | mod | admin
    bio = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())#DateTime(timezone=True) → タイムゾーン付き日時型 server_default=func.now() → DBサーバーが勝手に現在時刻を入れる つまり「ユーザーが登録された時間」が自動で残る
    