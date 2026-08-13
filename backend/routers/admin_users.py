import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.permissions import require_super_admin
from app.services.auth_service import AuthService, DuplicateUserError
from database import get_db
from app.repositories.auth_repository import AuthRepository
from app.repositories.audit_repository import AuditRepository

router = APIRouter()
logger = logging.getLogger("radiusflow.api.admin_users")


class AdminUserResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    last_login_at: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class CreateAdminUserRequest(BaseModel):
    username: str
    password: str
    role: str = "viewer"


class UpdateAdminUserRequest(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


@router.get("/admin/users", response_model=List[AdminUserResponse])
def list_admin_users(
    current_user: dict = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    repo = AuthRepository(db)
    users = repo.list_users()
    result = []
    for u in users:
        result.append(
            AdminUserResponse(
                id=u.id,
                username=u.username,
                role=u.role,
                is_active=u.is_active,
                last_login_at=u.last_login_at.isoformat() if u.last_login_at else None,
                created_at=u.created_at.isoformat() if u.created_at else None,
            )
        )
    return result


@router.post("/admin/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def create_admin_user(
    req: CreateAdminUserRequest,
    current_user: dict = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    auth_service = AuthService(db)
    try:
        user = auth_service.create_user(
            username=req.username,
            password=req.password,
            role=req.role,
        )
        AuditRepository(db).record(
            action="CREATE_ADMIN_USER",
            actor=current_user.get("sub"),
            resource_type="app_user",
            resource_id=user.username,
            details=f"Created user {user.username} with role {user.role}",
        )
        return AdminUserResponse(
            id=user.id,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
            created_at=user.created_at.isoformat() if user.created_at else None,
        )
    except DuplicateUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.put("/admin/users/{user_id}", response_model=AdminUserResponse)
def update_admin_user(
    user_id: int,
    req: UpdateAdminUserRequest,
    current_user: dict = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    repo = AuthRepository(db)
    user = repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if req.role is not None:
        user.role = req.role
    if req.is_active is not None:
        user.is_active = req.is_active

    if req.password:
        auth_service = AuthService(db)
        auth_service.change_password(user, req.password)
    else:
        db.commit()
        db.refresh(user)

    AuditRepository(db).record(
        action="UPDATE_ADMIN_USER",
        actor=current_user.get("sub"),
        resource_type="app_user",
        resource_id=user.username,
        details=f"Updated user {user.username}: role={user.role}, active={user.is_active}",
    )

    return AdminUserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.delete("/admin/users/{user_id}")
def delete_admin_user(
    user_id: int,
    current_user: dict = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    repo = AuthRepository(db)
    user = repo.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.username == current_user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own active session account",
        )

    username = user.username
    db.delete(user)
    db.commit()

    AuditRepository(db).record(
        action="DELETE_ADMIN_USER",
        actor=current_user.get("sub"),
        resource_type="app_user",
        resource_id=username,
        details=f"Deleted admin user {username}",
    )

    return {"status": "success", "message": f"User {username} deleted"}
