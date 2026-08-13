import secrets
import string
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.app.voucher import Voucher


class VoucherRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        code: str,
        group_name: Optional[str] = None,
        created_by: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> Voucher:
        voucher = Voucher(
            code=code,
            group_name=group_name,
            status="unused",
            created_by=created_by,
            expires_at=expires_at,
        )
        self.db.add(voucher)
        self.db.commit()
        self.db.refresh(voucher)
        return voucher

    def create_batch(
        self,
        count: int,
        group_name: Optional[str] = None,
        created_by: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> List[Voucher]:
        vouchers = []
        chars = string.ascii_uppercase + string.digits
        for _ in range(count):
            # Generate random 12-char code e.g. RF-XXXX-XXXX
            rand_part = "".join(secrets.choice(chars) for _ in range(8))
            code = f"RF-{rand_part[:4]}-{rand_part[4:]}"
            v = Voucher(
                code=code,
                group_name=group_name,
                status="unused",
                created_by=created_by,
                expires_at=expires_at,
            )
            self.db.add(v)
            vouchers.append(v)
        self.db.commit()
        for v in vouchers:
            self.db.refresh(v)
        return vouchers

    def get_by_code(self, code: str) -> Optional[Voucher]:
        return self.db.query(Voucher).filter(Voucher.code == code).first()

    def list_all(
        self,
        status: Optional[str] = None,
        group_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Voucher]:
        query = self.db.query(Voucher)
        if status and status != "all":
            query = query.filter(Voucher.status == status)
        if group_name and group_name != "all":
            query = query.filter(Voucher.group_name == group_name)
        return query.order_by(Voucher.created_at.desc()).offset(offset).limit(limit).all()

    def redeem(self, code: str, used_by: str) -> Optional[Voucher]:
        voucher = self.get_by_code(code)
        if not voucher or voucher.status != "unused":
            return None
        voucher.status = "used"
        voucher.used_by = used_by
        voucher.used_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(voucher)
        return voucher

    def delete(self, code: str) -> bool:
        voucher = self.get_by_code(code)
        if not voucher:
            return False
        self.db.delete(voucher)
        self.db.commit()
        return True
