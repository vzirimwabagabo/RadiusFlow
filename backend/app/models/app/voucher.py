from sqlalchemy import Column, DateTime, Integer, String, func
from database import Base


class Voucher(Base):
    __tablename__ = "app_vouchers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), nullable=False, unique=True, index=True)
    group_name = Column(String(64), nullable=True)
    status = Column(String(32), nullable=False, default="unused", index=True)  # unused, used, expired
    created_by = Column(String(64), nullable=True)
    used_by = Column(String(64), nullable=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
