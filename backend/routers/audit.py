from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.permissions import require_operator
from app.repositories.audit_repository import AuditRepository
from database import get_db

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: int
    action: str
    actor: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/audit-logs", response_model=List[AuditLogResponse])
def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_operator),
    db: Session = Depends(get_db),
):
    repo = AuditRepository(db)
    logs = repo.list_logs(limit=limit, offset=offset)
    result = []
    for log in logs:
        result.append(
            AuditLogResponse(
                id=log.id,
                action=log.action,
                actor=log.actor,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details,
                ip_address=log.ip_address,
                created_at=log.created_at.isoformat() if log.created_at else None,
            )
        )
    return result
