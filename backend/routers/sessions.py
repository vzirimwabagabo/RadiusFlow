"""Session accounting — radacct queries and stale session cleanup."""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import RadAcct

router = APIRouter()


@router.get("/sessions")
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(RadAcct).filter(
        RadAcct.acctstoptime.is_(None)
    ).order_by(RadAcct.acctstarttime.desc()).all()
    return [_session_dict(s) for s in sessions]


@router.get("/sessions/stale")
def get_stale(db: Session = Depends(get_db)):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=2)
    stale = db.query(RadAcct).filter(
        RadAcct.acctstoptime.is_(None),
        RadAcct.acctstarttime < cutoff
    ).all()
    return [_session_dict(s) for s in stale]


@router.post("/sessions/cleanup/stale")
def cleanup_stale(db: Session = Depends(get_db)):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=2)
    stale = db.query(RadAcct).filter(
        RadAcct.acctstoptime.is_(None),
        RadAcct.acctstarttime < cutoff
    ).all()
    now = datetime.now(timezone.utc)
    for s in stale:
        s.acctstoptime = now
    db.commit()
    return {"status": "success", "cleaned": len(stale), "message": f"Cleaned up {len(stale)} stale sessions"}


@router.get("/sessions/stale/summary")
def stale_summary(db: Session = Depends(get_db)):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=2)
    stale_count = db.query(RadAcct).filter(
        RadAcct.acctstoptime.is_(None), RadAcct.acctstarttime < cutoff
    ).count()
    total_active = db.query(RadAcct).filter(RadAcct.acctstoptime.is_(None)).count()
    return {"stale_count": stale_count, "total_active": total_active}


@router.get("/sessions/stale/users")
def stale_users(db: Session = Depends(get_db)):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=2)
    stale = db.query(RadAcct).filter(
        RadAcct.acctstoptime.is_(None), RadAcct.acctstarttime < cutoff
    ).all()
    return list(set(s.username for s in stale))


def _session_dict(s: RadAcct) -> dict:
    return {
        "radacctid": s.radacctid, "acctsessionid": s.acctsessionid,
        "acctuniqueid": s.acctuniqueid, "username": s.username,
        "realm": s.realm, "nasipaddress": str(s.nasipaddress),
        "acctstarttime": s.acctstarttime.isoformat() if s.acctstarttime else None,
        "acctupdatetime": s.acctupdatetime.isoformat() if s.acctupdatetime else None,
        "acctstoptime": s.acctstoptime.isoformat() if s.acctstoptime else None,
        "acctsessiontime": s.acctsessiontime,
        "acctinputoctets": s.acctinputoctets, "acctoutputoctets": s.acctoutputoctets,
        "framedipaddress": str(s.framedipaddress) if s.framedipaddress else None,
        "callingstationid": s.callingstationid,
        "calledstationid": s.calledstationid,
    }
