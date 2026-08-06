import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.services.auth_service import AuthService, InvalidCredentialsError
from auth import create_access_token, get_current_user
from config import settings
from database import get_db
from schemas import AdminLoginRequest, TokenResponse

router = APIRouter()
logger = logging.getLogger("radiusflow.api.auth")


@router.post("/auth/token", response_model=TokenResponse)
def login(req: AdminLoginRequest, request: Request, db: Session = Depends(get_db)):
    service = AuthService(db, session_hours=settings.AUTH_SESSION_HOURS)
    try:
        user = service.authenticate(req.username, req.password)
        session_token = service.start_session(
            user,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        ) from exc
    except Exception as exc:
        logger.exception("API management login failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        ) from exc

    return TokenResponse(
        access_token=create_access_token(
            {
                "uid": user.id,
                "sub": user.username,
                "role": user.role,
                "sid": session_token,
            }
        )
    )


@router.post("/auth/logout")
def logout(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    AuthService(
        db,
        session_hours=settings.AUTH_SESSION_HOURS,
    ).revoke_session(current_user["sid"])
    return {"status": "success", "message": "Signed out"}
