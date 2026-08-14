"""SQLAlchemy model for M-Pesa payment transactions in radiusflow.payments."""
from sqlalchemy import BigInteger, Column, DateTime, Integer, Numeric, String, Text, func
from database import Base


class Payment(Base):
    """Stores M-Pesa Express / STK Push transactions and callback results."""

    __tablename__ = "payments"
    __table_args__ = {"schema": "radiusflow"}

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    merchant_request_id = Column(String(128), nullable=False, index=True)
    checkout_request_id = Column(String(128), nullable=False, unique=True, index=True)
    phone_number = Column(String(20), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    mpesa_receipt_number = Column(String(64), nullable=True, index=True)
    transaction_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(32), nullable=False, default="PENDING", index=True)  # PENDING, SUCCESS, FAILED, CANCELLED
    result_code = Column(Integer, nullable=True)
    result_desc = Column(Text, nullable=True)
    user_id = Column(BigInteger, nullable=True)
    package_name = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
