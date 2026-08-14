"""
Safaricom Daraja 2.0 M-Pesa Integration Service
=================================================
Handles OAuth 2.0 token generation, M-Pesa Express (STK Push) initiation,
async callback webhook processing, and automatic subscriber package activation.
"""
import base64
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import requests
from sqlalchemy.orm import Session

from app.models.radiusflow.payment import Payment
from app.schemas.payment import STKPushRequest, STKPushResponse
from config import settings

logger = logging.getLogger("radiusflow.services.daraja")


def normalize_phone_number(phone: str) -> str:
    """Normalizes Kenyan phone numbers to format 254XXXXXXXXX."""
    cleaned = "".join(c for c in phone if c.isdigit())
    if cleaned.startswith("0") and len(cleaned) == 10:
        return "254" + cleaned[1:]
    if cleaned.startswith("254") and len(cleaned) == 12:
        return cleaned
    if len(cleaned) == 9:
        return "254" + cleaned
    return cleaned


class DarajaError(Exception):
    pass


class DarajaService:
    def __init__(self, db: Session):
        self.db = db
        self.env = (settings.DARAJA_ENVIRONMENT or "sandbox").lower()
        if self.env == "production":
            self.base_url = "https://api.safaricom.co.ke"
        else:
            self.base_url = "https://sandbox.safaricom.co.ke"

    def get_oauth_token(self) -> str:
        """Fetches OAuth 2.0 Access Token from Daraja API."""
        key = settings.DARAJA_CONSUMER_KEY
        secret = settings.DARAJA_CONSUMER_SECRET
        if not key or not secret:
            raise DarajaError("Daraja Consumer Key and Secret are not configured in settings.")

        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        try:
            resp = requests.get(url, auth=(key, secret), timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data["access_token"]
        except Exception as exc:
            logger.exception("Failed to obtain Daraja OAuth token")
            raise DarajaError(f"Failed to authenticate with Daraja API: {exc}") from exc

    def initiate_stk_push(
        self, req: STKPushRequest, user_id: Optional[int] = None
    ) -> STKPushResponse:
        """Initiates an M-Pesa Express (STK Push) request to the subscriber's phone."""
        phone = normalize_phone_number(req.phone_number)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        shortcode = settings.DARAJA_BUSINESS_SHORTCODE or "174379"
        passkey = settings.DARAJA_PASSKEY or "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"

        # Generate Base64 Password: Base64(Shortcode + Passkey + Timestamp)
        raw_password = f"{shortcode}{passkey}{timestamp}"
        password = base64.b64encode(raw_password.encode("utf-8")).decode("utf-8")

        token = self.get_oauth_token()
        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        payload = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": settings.DARAJA_TRANSACTION_TYPE or "CustomerPayBillOnline",
            "Amount": int(req.amount),
            "PartyA": phone,
            "PartyB": shortcode,
            "PhoneNumber": phone,
            "CallBackURL": settings.DARAJA_CALLBACK_URL,
            "AccountReference": (req.account_reference or "RadiusFlow")[:12],
            "TransactionDesc": f"Payment for {req.package_name or 'RadiusFlow Package'}"[:128],
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            resp_data = resp.json()
        except Exception as exc:
            logger.exception("Failed to send STK Push request to Daraja API")
            raise DarajaError(f"Network error initiating STK push: {exc}") from exc

        if resp.status_code != 200 or resp_data.get("ResponseCode") != "0":
            err_msg = resp_data.get("errorMessage") or resp_data.get("ResponseDescription") or "STK push rejected by Daraja"
            logger.warning("Daraja STK push rejected: %s", err_msg)
            raise DarajaError(err_msg)

        # Save PENDING record in radiusflow.payments
        merchant_id = resp_data["MerchantRequestID"]
        checkout_id = resp_data["CheckoutRequestID"]

        payment = Payment(
            merchant_request_id=merchant_id,
            checkout_request_id=checkout_id,
            phone_number=phone,
            amount=req.amount,
            status="PENDING",
            user_id=user_id,
            package_name=req.package_name,
        )
        self.db.add(payment)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            logger.exception("Failed to persist PENDING payment record")

        return STKPushResponse(
            merchant_request_id=merchant_id,
            checkout_request_id=checkout_id,
            response_code=resp_data.get("ResponseCode", "0"),
            response_description=resp_data.get("ResponseDescription", ""),
            customer_message=resp_data.get("CustomerMessage", "STK push sent to phone"),
        )

    def process_callback(self, callback_data: Dict[str, Any]) -> Payment | None:
        """
        Parses Safaricom M-Pesa stkCallback payload.
        Updates payment status to SUCCESS or FAILED in radiusflow.payments.
        """
        try:
            stk_callback = callback_data.get("Body", {}).get("stkCallback", {})
            checkout_id = stk_callback.get("CheckoutRequestID")
            result_code = stk_callback.get("ResultCode")
            result_desc = stk_callback.get("ResultDesc")

            if not checkout_id:
                logger.warning("Received Daraja callback missing CheckoutRequestID")
                return None

            payment = (
                self.db.query(Payment)
                .filter(Payment.checkout_request_id == checkout_id)
                .first()
            )
            if not payment:
                logger.warning("No payment record found for CheckoutRequestID=%s", checkout_id)
                return None

            payment.result_code = result_code
            payment.result_desc = result_desc

            if result_code == 0:
                payment.status = "SUCCESS"
                # Parse CallbackMetadata
                meta_items = stk_callback.get("CallbackMetadata", {}).get("Item", [])
                for item in meta_items:
                    name = item.get("Name")
                    val = item.get("Value")
                    if name == "MpesaReceiptNumber":
                        payment.mpesa_receipt_number = str(val)
                    elif name == "TransactionDate":
                        try:
                            # e.g. 20260814231500
                            dt_str = str(val)
                            payment.transaction_date = datetime.strptime(dt_str, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
                        except Exception:
                            pass

                logger.info(
                    "M-Pesa payment SUCCESS: Receipt=%s Amount=%s Phone=%s",
                    payment.mpesa_receipt_number,
                    payment.amount,
                    payment.phone_number,
                )
            else:
                payment.status = "FAILED" if result_code != 1032 else "CANCELLED"
                logger.info("M-Pesa payment %s: ResultCode=%s Desc=%s", payment.status, result_code, result_desc)

            self.db.commit()
            return payment

        except Exception as exc:
            self.db.rollback()
            logger.exception("Failed to process Daraja callback")
            raise DarajaError(f"Callback processing error: {exc}") from exc

    def get_payment_status(self, checkout_request_id: str) -> Payment | None:
        """Retrieves payment status by checkout_request_id."""
        return (
            self.db.query(Payment)
            .filter(Payment.checkout_request_id == checkout_request_id)
            .first()
        )

    def list_payments(
        self,
        status: Optional[str] = None,
        phone_number: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Payment]:
        """Lists payment records with filtering."""
        query = self.db.query(Payment)
        if status:
            query = query.filter(Payment.status == status.upper())
        if phone_number:
            phone_clean = normalize_phone_number(phone_number)
            query = query.filter(Payment.phone_number.contains(phone_clean))
        return (
            query.order_by(Payment.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
