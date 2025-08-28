from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from . import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)

    actor_id    = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # 管理操作の実行者
    action      = Column(String(100), nullable=False)   # 例: 'post_unpublish', 'user_ban'
    target_type = Column(String(20),  nullable=False)   # 'article' | 'comment' | 'user' など
    target_id   = Column(Integer,      nullable=True)   # 対象のPK（任意）
    meta        = Column(JSONB,        nullable=True)   # 任意の追加情報（差分など）

    created_at  = Column(DateTime(timezone=True), server_default=func.now())
