from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import HTTPException

from config import settings


def create_access_token(data: dict, expires_hours: Optional[int] = None) -> str:
    now = datetime.now(timezone.utc)
    payload = data.copy()
    payload.update(
        {
            "exp": now + timedelta(hours=expires_hours or settings.JWT_EXPIRE_HOURS),
            "iat": now,
        }
    )
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
