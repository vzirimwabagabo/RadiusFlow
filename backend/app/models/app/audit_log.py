from dataclasses import dataclass
from datetime import datetime


@dataclass
class AuditLog:
    action: str
    actor: str | None = None
    created_at: datetime | None = None
