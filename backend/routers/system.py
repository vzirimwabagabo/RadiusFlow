"""System endpoints — root and health check."""
import socket
import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

router = APIRouter()


def _check_port(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


@router.get("/health")
def health(db: Session = Depends(get_db)):
    start_time = time.time()
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    latency_ms = round((time.time() - start_time) * 1000, 2)
    overall = "healthy" if db_ok else "degraded"

    return {
        "status": overall,
        "postgresql": "reachable" if db_ok else "unreachable",
        "db_latency_ms": latency_ms,
        "freeradius": "managed_vps",
        "api_service": "online",
        "version": "1.0.0",
        "environment": "production",
    }
