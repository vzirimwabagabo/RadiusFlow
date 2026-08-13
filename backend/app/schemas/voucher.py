from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class VoucherResponse(BaseModel):
    id: int
    code: str
    group_name: Optional[str] = None
    status: str = "unused"
    created_by: Optional[str] = None
    used_by: Optional[str] = None
    used_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VoucherGenerateRequest(BaseModel):
    count: int = Field(default=5, ge=1, le=100)
    group_name: Optional[str] = None
    expires_in_days: Optional[int] = Field(default=30, ge=1, le=365)


class VoucherRedeemRequest(BaseModel):
    code: str
    username: str
