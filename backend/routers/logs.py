"""Authentication logs — radpostauth."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import RadPostAuth

router = APIRouter()


@router.get("/logs/auth")
def get_auth_logs(limit: int = 100, db: Session = Depends(get_db)):
    logs = db.query(RadPostAuth).order_by(
        RadPostAuth.authdate.desc()
    ).limit(limit).all()
    return [_log_dict(l) for l in logs]


@router.get("/logs/failed-attempts")
def failed_attempts(db: Session = Depends(get_db)):
    count = db.query(RadPostAuth).filter(RadPostAuth.reply == "Access-Reject").count()
    return {"failed_count": count}


def _log_dict(l: RadPostAuth) -> dict:
    return {
        "id": l.id, "username": l.username,
        "reply": l.reply,
        "authdate": l.authdate.isoformat() if l.authdate else None,
        "calledstationid": l.calledstationid,
        "callingstationid": l.callingstationid,
        "class": l.class_,
    }
