from sqlalchemy import Column, Integer, String, DateTime, func, UniqueConstraint
from . import Base

class University(Base):
    __tablename__ = "universities"

    id     = Column(Integer, primary_key=True)
    name   = Column(String(200), nullable=False)
    domain = Column(String(255), nullable=False)  # 例: 'u-aizu.ac.jp'

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("domain", name="uq_universities_domain"),
    )
