"""Monitoring — dashboard stats, traffic, online users, revenue."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import RadAcct

router = APIRouter()


@router.get("/monitor/online-users")
def online_users(db: Session = Depends(get_db)):
    count = db.query(RadAcct).filter(RadAcct.acctstoptime.is_(None)).count()
    return {"online_users": count}


@router.get("/monitor/traffic-stats")
def traffic_stats(db: Session = Depends(get_db)):
    active = db.query(RadAcct).filter(RadAcct.acctstoptime.is_(None)).all()
    total_down = sum(s.acctinputoctets or 0 for s in active)
    total_up = sum(s.acctoutputoctets or 0 for s in active)
    return {
        "total_download": total_down,
        "total_upload": total_up,
        "active_sessions": len(active),
    }


@router.get("/monitor/dashboard")
def dashboard():
    raise HTTPException(
        status_code=503,
        detail=(
            "Dashboard reporting is disabled until the verified read-only "
            "production queries are approved."
        ),
    )


@router.get("/monitor/revenue")
def revenue(db: Session = Depends(get_db)):
    # Revenue calculation depends on your billing model.
    # This counts completed sessions and could be extended to join with a billing table.
    stopped = db.query(RadAcct).filter(RadAcct.acctstoptime.is_not(None)).count()
    return {"total_sessions": stopped, "currency": "KES", "note": "Connect a billing table for revenue"}
