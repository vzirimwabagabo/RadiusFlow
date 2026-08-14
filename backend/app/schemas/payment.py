"""Pydantic schemas for Safaricom Daraja M-Pesa STK Push and callback processing."""
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class STKPushRequest(BaseModel):
    phone_number: str = Field(..., min_length=9, max_length=15, examples=["254708374149", "0708374149"])
    amount: float = Field(..., gt=0, examples=[100.0])
    package_name: Optional[str] = Field(default=None, examples=["Monthly-10Mbps"])
    account_reference: Optional[str] = Field(default="RadiusFlow", max_length=12, examples=["RadiusFlow"])


class STKPushResponse(BaseModel):
    merchant_request_id: str
    checkout_request_id: str
    response_code: str
    response_description: str
    customer_message: str


class PaymentResponse(BaseModel):
    id: int
    merchant_request_id: str
    checkout_request_id: str
    phone_number: str
    amount: float
    mpesa_receipt_number: Optional[str] = None
    status: str
    result_code: Optional[int] = None
    result_desc: Optional[str] = None
    package_name: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
