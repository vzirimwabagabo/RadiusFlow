from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.permissions import require_operator
from app.repositories.audit_repository import AuditRepository
from app.schemas.voucher import VoucherGenerateRequest, VoucherRedeemRequest, VoucherResponse
from app.services.voucher_service import VoucherService
from database import get_db

router = APIRouter()


@router.get("/vouchers", response_model=List[VoucherResponse])
def list_vouchers(
    status_val: Optional[str] = Query(default=None, alias="status"),
    group_name: Optional[str] = Query(default=None, alias="group_name"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_operator),
    db: Session = Depends(get_db),
):
    service = VoucherService(db)
    return service.list_vouchers(status=status_val, group_name=group_name, limit=limit, offset=offset)


@router.post("/vouchers/generate", response_model=List[VoucherResponse], status_code=status.HTTP_201_CREATED)
def generate_vouchers(
    req: VoucherGenerateRequest,
    current_user: dict = Depends(require_operator),
    db: Session = Depends(get_db),
):
    service = VoucherService(db)
    actor = current_user.get("sub")
    vouchers = service.generate_vouchers(req, created_by=actor)

    AuditRepository(db).record(
        action="GENERATE_VOUCHERS",
        actor=actor,
        resource_type="voucher_batch",
        resource_id=req.group_name or "default",
        details=f"Generated {len(vouchers)} vouchers for group {req.group_name or 'unspecified'}",
    )

    return vouchers


@router.post("/vouchers/redeem", response_model=VoucherResponse)
def redeem_voucher(
    req: VoucherRedeemRequest,
    current_user: dict = Depends(require_operator),
    db: Session = Depends(get_db),
):
    service = VoucherService(db)
    voucher = service.redeem_voucher(req)
    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used voucher code",
        )

    AuditRepository(db).record(
        action="REDEEM_VOUCHER",
        actor=current_user.get("sub"),
        resource_type="voucher",
        resource_id=req.code,
        details=f"Redeemed voucher {req.code} for user {req.username}",
    )

    return voucher


@router.delete("/vouchers/{code}")
def delete_voucher(
    code: str,
    current_user: dict = Depends(require_operator),
    db: Session = Depends(get_db),
):
    service = VoucherService(db)
    success = service.delete_voucher(code)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voucher not found",
        )

    AuditRepository(db).record(
        action="DELETE_VOUCHER",
        actor=current_user.get("sub"),
        resource_type="voucher",
        resource_id=code,
        details=f"Deleted voucher {code}",
    )

    return {"status": "success", "message": f"Voucher {code} deleted"}
