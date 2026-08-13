from sqlalchemy.orm import Session
from app.models.app.audit_log import AuditLog
from typing import Optional, List


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        action: str,
        actor: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        log_entry = AuditLog(
            action=action,
            actor=actor,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
        )
        self.db.add(log_entry)
        try:
            self.db.commit()
            self.db.refresh(log_entry)
            return log_entry
        except Exception:
            self.db.rollback()
            raise

    def list_logs(self, limit: int = 100, offset: int = 0) -> List[AuditLog]:
        return (
            self.db.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
