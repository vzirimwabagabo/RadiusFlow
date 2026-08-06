"""JWT authentication backed by revocable management sessions."""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.jwt import create_access_token, verify_token
from app.services.auth_service import AuthService
from config import settings
from database import get_db

security = HTTPBearer(auto_error=False)
logger = logging.getLogger("radiusflow.api.auth")


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = verify_token(credentials.credentials)
    session_token = payload.get("sid")
    try:
        resolved = AuthService(
            db,
            session_hours=settings.AUTH_SESSION_HOURS,
        ).resolve_session(session_token)
    except Exception as exc:
        logger.exception("Unable to validate API management session")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        ) from exc

    if (
        not resolved
        or payload.get("uid") != resolved.user.id
        or payload.get("sub") != resolved.user.username
        or payload.get("role") != resolved.user.role
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is invalid or expired",
        )

    return {
        "uid": resolved.user.id,
        "sub": resolved.user.username,
        "role": resolved.user.role,
        "sid": session_token,
    }


__all__ = [
    "create_access_token",
    "get_current_user",
    "security",
    "verify_token",
]
