from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.voucher_repository import VoucherRepository
from app.schemas.voucher import VoucherGenerateRequest, VoucherRedeemRequest, VoucherResponse


class VoucherService:
    def __init__(self, db: Session):
        self.repo = VoucherRepository(db)

    def list_vouchers(
        self,
        status: Optional[str] = None,
        group_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[VoucherResponse]:
        vouchers = self.repo.list_all(status=status, group_name=group_name, limit=limit, offset=offset)
        return [VoucherResponse.model_validate(v) for v in vouchers]

    def generate_vouchers(
        self,
        req: VoucherGenerateRequest,
        created_by: Optional[str] = None,
    ) -> List[VoucherResponse]:
        expires_at = None
        if req.expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=req.expires_in_days)
        vouchers = self.repo.create_batch(
            count=req.count,
            group_name=req.group_name,
            created_by=created_by,
            expires_at=expires_at,
        )
        return [VoucherResponse.model_validate(v) for v in vouchers]

    def redeem_voucher(self, req: VoucherRedeemRequest) -> Optional[VoucherResponse]:
        voucher = self.repo.redeem(req.code.strip(), req.username.strip())
        if not voucher:
            return None
        return VoucherResponse.model_validate(voucher)

    def delete_voucher(self, code: str) -> bool:
        return self.repo.delete(code)
