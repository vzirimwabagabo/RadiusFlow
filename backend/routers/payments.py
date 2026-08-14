"""API Router for Safaricom Daraja M-Pesa Payments."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.permissions import require_operator, require_viewer
from app.repositories.audit_repository import AuditRepository
from app.schemas.payment import PaymentResponse, STKPushRequest, STKPushResponse
from app.services.daraja_service import DarajaError, DarajaService
from database import get_db

router = APIRouter()


@router.post("/payments/stk-push", response_model=STKPushResponse, status_code=status.HTTP_200_OK)
def initiate_stk_push(
    req: STKPushRequest,
    current_user: dict = Depends(require_operator),
    db: Session = Depends(get_db),
):
    """Initiates an M-Pesa Express (STK Push) prompt on subscriber's phone."""
    service = DarajaService(db)
    actor = current_user.get("sub")
    try:
        res = service.initiate_stk_push(req)
        AuditRepository(db).record(
            action="INITIATE_STK_PUSH",
            actor=actor,
            resource_type="payment",
            resource_id=res.checkout_request_id,
            details=f"Initiated STK Push KES {req.amount} to {req.phone_number} for package {req.package_name or 'Default'}",
        )
        return res
    except DarajaError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/payments/callback")
def process_m_pesa_callback(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """
    Public webhook receiver for Safaricom Daraja async callback notifications.
    Safaricom sends JSON payload containing transaction results.
    """
    service = DarajaService(db)
    try:
        payment = service.process_callback(payload)
        return {"ResultCode": 0, "ResultDesc": "Callback processed successfully"}
    except Exception as exc:
        return {"ResultCode": 1, "ResultDesc": f"Callback processing failed: {exc}"}


@router.get("/payments/status/{checkout_request_id}", response_model=PaymentResponse)
def get_payment_status(
    checkout_request_id: str,
    current_user: dict = Depends(require_viewer),
    db: Session = Depends(get_db),
):
    """Retrieves current status of an M-Pesa payment transaction."""
    service = DarajaService(db)
    payment = service.get_payment_status(checkout_request_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment transaction not found",
        )
    return payment


@router.get("/payments", response_model=List[PaymentResponse])
def list_payments(
    status_val: Optional[str] = Query(default=None, alias="status"),
    phone: Optional[str] = Query(default=None, alias="phone"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_viewer),
    db: Session = Depends(get_db),
):
    """Lists M-Pesa payment transactions for administration and accounting."""
    service = DarajaService(db)
    return service.list_payments(status=status_val, phone_number=phone, limit=limit, offset=offset)
