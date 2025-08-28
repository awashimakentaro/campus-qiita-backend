from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, CheckConstraint, Index
from . import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)

    target_type = Column(String(20), nullable=False)   # 'article' | 'comment'
    target_id   = Column(Integer,      nullable=False) # 対象のPK
    reporter_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    reason = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="open")  # 'open' | 'triage' | 'closed'

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("target_type IN ('article','comment')", name="ck_reports_target_type"),
        CheckConstraint("status IN ('open','triage','closed')", name="ck_reports_status"),
        Index("ix_reports_target", "target_type", "target_id"),
        Index("ix_reports_reporter_id", "reporter_id"),
    )
