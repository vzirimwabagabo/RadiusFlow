"""SMS sending — Africa's Talking API integration."""
import httpx
from fastapi import APIRouter, Depends, HTTPException
from config import settings
from schemas import SMSRequest

router = APIRouter()


@router.post("/send-sms")
async def send_sms(req: SMSRequest):
    if not settings.SMS_API_KEY:
        raise HTTPException(503, "SMS not configured — set SMS_API_KEY and SMS_USERNAME")
    url = "https://api.africastalking.com/version1/messaging"
    headers = {
        "apiKey": settings.SMS_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    data = {
        "username": settings.SMS_USERNAME,
        "to": req.phone,
        "message": req.message,
        "from": settings.SMS_SENDER_ID,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, data=data)
    if resp.status_code != 201:
        raise HTTPException(502, f"SMS send failed: {resp.text}")
    return {"status": "success", "message": f"SMS sent to {req.phone}"}