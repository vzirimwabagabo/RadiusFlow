from pydantic import BaseModel, ConfigDict
from pydantic import Field
from typing import Optional
from datetime import datetime


# --- Users ---
class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64, examples=["customer001"])
    password: str = Field(..., min_length=1, max_length=253, examples=["strong-password"])
    group_name: Optional[str] = None
    rate_limit: Optional[str] = Field(default=None, examples=["10M/10M"])
    session_timeout: Optional[int] = Field(default=None, ge=1)
    max_down: Optional[int] = Field(default=None, ge=1)
    max_up: Optional[int] = Field(default=None, ge=1)
    idle_timeout: Optional[int] = Field(default=None, ge=1)
    expiration: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(active|blocked)$")


class CreateUserWithPackageRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=253)
    package_name: str = Field(..., min_length=1, max_length=64)
    validity_days: Optional[int] = Field(default=None, ge=1)
    status: Optional[str] = Field(default=None, pattern="^(active|blocked)$")


class UpdateUserRequest(BaseModel):
    password: Optional[str] = None
    rate_limit: Optional[str] = None
    session_timeout: Optional[int] = Field(default=None, ge=1)
    max_down: Optional[int] = Field(default=None, ge=1)
    max_up: Optional[int] = Field(default=None, ge=1)
    idle_timeout: Optional[int] = Field(default=None, ge=1)
    status: Optional[str] = Field(default=None, pattern="^(active|blocked)$")


class SetExpirationRequest(BaseModel):
    expiration: datetime


class ExtendExpirationRequest(BaseModel):
    days: int = Field(..., ge=1)


class RenewPackageRequest(BaseModel):
    package_name: Optional[str] = None
    validity_days: Optional[int] = Field(default=None, ge=1)


class ChangePackageRequest(BaseModel):
    package_name: str = Field(..., min_length=1, max_length=64)


class AdminLoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    username: str
    # password is intentionally excluded — Cleartext-Password must never leave the server.
    group_name: Optional[str] = None
    rate_limit: Optional[str] = None
    session_timeout: Optional[int] = None
    max_down: Optional[int] = None
    max_up: Optional[int] = None
    idle_timeout: Optional[int] = None
    expiration: Optional[str] = None
    status: str = "active"

    model_config = ConfigDict(from_attributes=True)


# --- Activity ---
class LiveActivityResponse(BaseModel):
    username: Optional[str] = None
    nasipaddress: Optional[str] = None     
    framedipaddress: Optional[str] = None   
    callingstationid: Optional[str] = None
    acctstarttime: Optional[datetime] = None
    acctinputoctets: Optional[int] = None
    acctoutputoctets: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# --- Groups / Packages ---
class CreateGroupRequest(BaseModel):
    groupname: Optional[str] = None
    rate_limit: Optional[str] = None
    session_timeout: Optional[int] = Field(default=None, ge=1)
    max_down: Optional[int] = Field(default=None, ge=1)
    max_up: Optional[int] = Field(default=None, ge=1)
    idle_timeout: Optional[int] = Field(default=None, ge=1)


class GroupResponse(BaseModel):
    groupname: str
    rate_limit: Optional[str] = None
    session_timeout: Optional[int] = None
    max_down: Optional[int] = None
    max_up: Optional[int] = None
    idle_timeout: Optional[int] = None
    user_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# --- NAS ---
class CreateNASRequest(BaseModel):
    nasname: str = Field(..., min_length=1, max_length=128, examples=["192.0.2.10"])
    shortname: str = Field(..., min_length=1, max_length=32, examples=["main-router"])
    secret: str = Field(..., min_length=1, max_length=60)
    type: str = Field(default="other", max_length=30)
    ports: Optional[int] = Field(default=1812, ge=1, le=65535)
    server: Optional[str] = None
    community: Optional[str] = None
    description: Optional[str] = None

class NasResponse(BaseModel):
    id: int
    nasname: str
    shortname: str
    type: str
    ports: Optional[int] = None
    # secret is intentionally excluded — the RADIUS shared secret must never leave the server.
    secret_configured: bool
    server: Optional[str] = None
    community: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Backward-compatible names from the first schema draft.
UserCreate = CreateUserRequest
NasCreate = CreateNASRequest


# --- SMS ---
class SMSRequest(BaseModel):
    phone: str = Field(..., min_length=7, max_length=20, examples=["+254700000000"])
    message: str = Field(..., min_length=1, max_length=480)

