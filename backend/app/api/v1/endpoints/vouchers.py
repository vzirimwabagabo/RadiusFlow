from fastapi import APIRouter

router = APIRouter(prefix="/vouchers", tags=["Vouchers"])


@router.get("")
def list_vouchers():
    return {
        "items": [],
        "message": "Voucher management is not implemented yet. Use user/package endpoints first.",
    }
