"""User management endpoints — radcheck, radreply, radusergroup."""
import re
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from models import RadCheck, RadGroupCheck, RadReply, RadUserGroup, RadGroupReply, RadAcct, NAS
from schemas import (
    CreateUserRequest, CreateUserWithPackageRequest, UpdateUserRequest,
    SetExpirationRequest, ExtendExpirationRequest, RenewPackageRequest,
    ChangePackageRequest, UserResponse,
)
from coa import disconnect_user

router = APIRouter()


def _format_expiration(dt: datetime) -> str:
    """FreeRADIUS expects: '01 Aug 2026 00:00:00'"""
    return dt.strftime("%d %b %Y %H:%M:%S")


def _build_user_response(db: Session, username: str) -> dict:
    checks = db.query(RadCheck).filter(RadCheck.username == username).all()
    replies = db.query(RadReply).filter(RadReply.username == username).all()
    ug = db.query(RadUserGroup).filter(RadUserGroup.username == username).first()
    check_map = {c.attribute: c.value for c in checks}
    reply_map = {r.attribute: r.value for r in replies}

    expiration = check_map.get("Expiration")
    status = "active"
    if check_map.get("Auth-Type") == "Reject":
        status = "blocked"
    elif expiration:
        try:
            exp_dt = datetime.strptime(expiration, "%d %b %Y %H:%M:%S")
            if exp_dt < datetime.now():
                status = "expired"
        except ValueError:
            pass

    return UserResponse(
        username=username,
        # password intentionally omitted — Cleartext-Password must never leave the server.
        group_name=ug.groupname if ug else None,
        rate_limit=reply_map.get("Mikrotik-Rate-Limit"),
        session_timeout=int(reply_map["Session-Timeout"]) if reply_map.get("Session-Timeout") else None,
        max_down=int(reply_map["WISPr-Bandwidth-Max-Down"]) if reply_map.get("WISPr-Bandwidth-Max-Down") else None,
        max_up=int(reply_map["WISPr-Bandwidth-Max-Up"]) if reply_map.get("WISPr-Bandwidth-Max-Up") else None,
        idle_timeout=int(reply_map["Idle-Timeout"]) if reply_map.get("Idle-Timeout") else None,
        expiration=expiration,
        status=status,
    ).model_dump()


def _set_check_attr(db: Session, username: str, attribute: str, op: str, value: str):
    db.query(RadCheck).filter(RadCheck.username == username, RadCheck.attribute == attribute).delete()
    db.add(RadCheck(username=username, attribute=attribute, op=op, value=value))


def _set_reply_attr(db: Session, username: str, attribute: str, op: str, value: str):
    db.query(RadReply).filter(RadReply.username == username, RadReply.attribute == attribute).delete()
    db.add(RadReply(username=username, attribute=attribute, op=op, value=str(value)))


def _parse_expiration_value(value: str) -> datetime:
    normalized = (value or "").strip()
    if not normalized:
        raise HTTPException(400, "expiration must not be empty")

    relative_match = re.fullmatch(r"(?i)(\d+)\s*(min|mins|minute|minutes|hour|hours|day|days)", normalized)
    if relative_match:
        amount = int(relative_match.group(1))
        unit = relative_match.group(2).lower()
        if unit.startswith("min"):
            return datetime.now() + timedelta(minutes=amount)
        if unit.startswith("hour"):
            return datetime.now() + timedelta(hours=amount)
        return datetime.now() + timedelta(days=amount)

    try:
        return datetime.fromisoformat(normalized.replace("Z", ""))
    except ValueError as exc:
        raise HTTPException(
            400,
            "expiration must be an ISO date/datetime like '2026-08-03' or a relative value like '30 mins'",
        ) from exc


@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    usernames = db.query(RadCheck.username).distinct().all()
    return [_build_user_response(db, u[0]) for u in usernames]


@router.post("/users")
def create_user(req: CreateUserRequest, db: Session = Depends(get_db)):
    existing = db.query(RadCheck).filter(RadCheck.username == req.username).first()
    if existing:
        raise HTTPException(409, f"User '{req.username}' already exists")
    _set_check_attr(db, req.username, "Cleartext-Password", ":=", req.password)
    if req.group_name:
        db.add(RadUserGroup(username=req.username, groupname=req.group_name, priority=1))
    if req.rate_limit:
        _set_reply_attr(db, req.username, "Mikrotik-Rate-Limit", "=", req.rate_limit)
    if req.session_timeout:
        _set_reply_attr(db, req.username, "Session-Timeout", "=", req.session_timeout)
    if req.max_down:
        _set_reply_attr(db, req.username, "WISPr-Bandwidth-Max-Down", "=", req.max_down)
    if req.max_up:
        _set_reply_attr(db, req.username, "WISPr-Bandwidth-Max-Up", "=", req.max_up)
    if req.idle_timeout:
        _set_reply_attr(db, req.username, "Idle-Timeout", "=", req.idle_timeout)
    if req.expiration:
        dt = _parse_expiration_value(req.expiration)
        _set_check_attr(db, req.username, "Expiration", ":=", _format_expiration(dt))
    if req.status == "blocked":
        _set_check_attr(db, req.username, "Auth-Type", ":=", "Reject")
    elif req.status == "active":
        db.query(RadCheck).filter(RadCheck.username == req.username, RadCheck.attribute == "Auth-Type").delete()
    db.commit()
    return _build_user_response(db, req.username)


@router.post("/users/with-package")
def create_user_with_package(req: CreateUserWithPackageRequest, db: Session = Depends(get_db)):
    existing = db.query(RadCheck).filter(RadCheck.username == req.username).first()
    if existing:
        raise HTTPException(409, f"User '{req.username}' already exists")
    group_replies = db.query(RadGroupReply).filter(RadGroupReply.groupname == req.package_name).all()
    if not group_replies:
        raise HTTPException(404, f"Package '{req.package_name}' not found")
    _set_check_attr(db, req.username, "Cleartext-Password", ":=", req.password)
    db.add(RadUserGroup(username=req.username, groupname=req.package_name, priority=1))
    days = req.validity_days or 1
    exp_dt = datetime.now() + timedelta(days=days)
    _set_check_attr(db, req.username, "Expiration", ":=", _format_expiration(exp_dt))
    if req.status == "blocked":
        _set_check_attr(db, req.username, "Auth-Type", ":=", "Reject")
    elif req.status == "active":
        db.query(RadCheck).filter(RadCheck.username == req.username, RadCheck.attribute == "Auth-Type").delete()
    for gr in group_replies:
        db.add(RadReply(username=req.username, attribute=gr.attribute, op=gr.op, value=gr.value))
    db.commit()
    return _build_user_response(db, req.username)


@router.get("/users/expired")
def get_expired_users(db: Session = Depends(get_db)):
    now_str = _format_expiration(datetime.now())
    expired = db.query(RadCheck).filter(
        RadCheck.attribute == "Expiration", RadCheck.value < now_str
    ).all()
    return [_build_user_response(db, c.username) for c in expired]


@router.get("/users/expiring-soon")
def get_expiring_soon(db: Session = Depends(get_db)):
    now = datetime.now()
    cutoff = now + timedelta(hours=24)
    checks = db.query(RadCheck).filter(RadCheck.attribute == "Expiration").all()
    result = []
    for c in checks:
        try:
            exp_dt = datetime.strptime(c.value, "%d %b %Y %H:%M:%S")
            if now < exp_dt < cutoff:
                result.append(_build_user_response(db, c.username))
        except ValueError:
            continue
    return result


@router.get("/users/{username}")
def get_user(username: str, db: Session = Depends(get_db)):
    if not db.query(RadCheck).filter(RadCheck.username == username).first():
        raise HTTPException(404, f"User '{username}' not found")
    return _build_user_response(db, username)


@router.put("/users/{username}")
def update_user(username: str, req: UpdateUserRequest, db: Session = Depends(get_db)):
    if not db.query(RadCheck).filter(RadCheck.username == username).first():
        raise HTTPException(404, f"User '{username}' not found")
    if req.password:
        _set_check_attr(db, username, "Cleartext-Password", ":=", req.password)
    if req.rate_limit:
        _set_reply_attr(db, username, "Mikrotik-Rate-Limit", "=", req.rate_limit)
    if req.session_timeout is not None:
        _set_reply_attr(db, username, "Session-Timeout", "=", req.session_timeout)
    if req.max_down is not None:
        _set_reply_attr(db, username, "WISPr-Bandwidth-Max-Down", "=", req.max_down)
    if req.max_up is not None:
        _set_reply_attr(db, username, "WISPr-Bandwidth-Max-Up", "=", req.max_up)
    if req.idle_timeout is not None:
        _set_reply_attr(db, username, "Idle-Timeout", "=", req.idle_timeout)
    if req.status == "blocked":
        _set_check_attr(db, username, "Auth-Type", ":=", "Reject")
    elif req.status == "active":
        db.query(RadCheck).filter(RadCheck.username == username, RadCheck.attribute == "Auth-Type").delete()
    db.commit()
    return _build_user_response(db, username)


@router.delete("/users/{username}")
def delete_user(username: str, db: Session = Depends(get_db)):
    if not db.query(RadCheck).filter(RadCheck.username == username).first():
        raise HTTPException(404, f"User '{username}' not found")
    db.query(RadCheck).filter(RadCheck.username == username).delete()
    db.query(RadReply).filter(RadReply.username == username).delete()
    db.query(RadUserGroup).filter(RadUserGroup.username == username).delete()
    db.commit()
    return {"status": "success", "message": f"User '{username}' deleted"}


@router.post("/users/{username}/block")
def block_user(username: str, db: Session = Depends(get_db)):
    if not db.query(RadCheck).filter(RadCheck.username == username).first():
        raise HTTPException(404, f"User '{username}' not found")
    _set_check_attr(db, username, "Auth-Type", ":=", "Reject")
    db.commit()
    return {"status": "success", "message": f"User '{username}' blocked (Auth-Type := Reject)"}


@router.delete("/users/{username}/block")
def unblock_user(username: str, db: Session = Depends(get_db)):
    if not db.query(RadCheck).filter(RadCheck.username == username).first():
        raise HTTPException(404, f"User '{username}' not found")
    db.query(RadCheck).filter(RadCheck.username == username, RadCheck.attribute == "Auth-Type").delete()
    db.commit()
    return {"status": "success", "message": f"User '{username}' unblocked"}


@router.post("/users/{username}/expiration")
def set_expiration(username: str, req: SetExpirationRequest, db: Session = Depends(get_db)):
    if not db.query(RadCheck).filter(RadCheck.username == username).first():
        raise HTTPException(404, f"User '{username}' not found")
    _set_check_attr(db, username, "Expiration", ":=", _format_expiration(req.expiration))
    db.commit()
    return {"status": "success", "message": f"Expiration set to {req.expiration} for '{username}'"}


@router.post("/users/{username}/extend")
def extend_user(username: str, req: ExtendExpirationRequest, db: Session = Depends(get_db)):
    if not db.query(RadCheck).filter(RadCheck.username == username).first():
        raise HTTPException(404, f"User '{username}' not found")
    existing = db.query(RadCheck).filter(
        RadCheck.username == username, RadCheck.attribute == "Expiration"
    ).first()
    if existing:
        base = datetime.strptime(existing.value, "%d %b %Y %H:%M:%S")
    else:
        base = datetime.now()
    new_exp = base + timedelta(days=req.days)
    _set_check_attr(db, username, "Expiration", ":=", _format_expiration(new_exp))
    db.commit()
    return {"status": "success", "message": f"Extended '{username}' by {req.days} day(s)", "expiration": new_exp.isoformat()}


@router.post("/users/{username}/renew")
def renew_user(username: str, req: RenewPackageRequest, db: Session = Depends(get_db)):
    if not db.query(RadCheck).filter(RadCheck.username == username).first():
        raise HTTPException(404, f"User '{username}' not found")
    days = req.validity_days or 1
    if req.package_name:
        group_replies = db.query(RadGroupReply).filter(RadGroupReply.groupname == req.package_name).all()
        if not group_replies:
            raise HTTPException(404, f"Package '{req.package_name}' not found")
        ug = db.query(RadUserGroup).filter(RadUserGroup.username == username).first()
        if ug:
            ug.groupname = req.package_name
        else:
            db.add(RadUserGroup(username=username, groupname=req.package_name, priority=1))
        db.query(RadReply).filter(RadReply.username == username).delete()
        for gr in group_replies:
            db.add(RadReply(username=username, attribute=gr.attribute, op=gr.op, value=gr.value))
        gr_check = db.query(RadGroupCheck).filter(RadGroupCheck.groupname == req.package_name).all()
        for gc in gr_check:
            _set_check_attr(db, username, gc.attribute, gc.op, gc.value)
    new_exp = datetime.now() + timedelta(days=days)
    _set_check_attr(db, username, "Expiration", ":=", _format_expiration(new_exp))
    db.commit()
    return {"status": "success", "message": f"User '{username}' renewed for {days} day(s)", "expiration": new_exp.isoformat()}


@router.post("/users/{username}/change-package")
def change_package(username: str, req: ChangePackageRequest, db: Session = Depends(get_db)):
    if not db.query(RadCheck).filter(RadCheck.username == username).first():
        raise HTTPException(404, f"User '{username}' not found")
    group_replies = db.query(RadGroupReply).filter(RadGroupReply.groupname == req.package_name).all()
    if not group_replies:
        raise HTTPException(404, f"Package '{req.package_name}' not found")
    ug = db.query(RadUserGroup).filter(RadUserGroup.username == username).first()
    if ug:
        ug.groupname = req.package_name
    else:
        db.add(RadUserGroup(username=username, groupname=req.package_name, priority=1))
    db.query(RadReply).filter(RadReply.username == username).delete()
    for gr in group_replies:
        db.add(RadReply(username=username, attribute=gr.attribute, op=gr.op, value=gr.value))
    db.commit()
    return {"status": "success", "message": f"Package changed to '{req.package_name}' for '{username}'"}


@router.post("/users/{username}/disconnect")
def disconnect_session(username: str, db: Session = Depends(get_db)):
    active = db.query(RadAcct).filter(
        RadAcct.username == username, RadAcct.acctstoptime.is_(None)
    ).order_by(RadAcct.acctstarttime.desc()).first()
    if not active:
        raise HTTPException(404, f"No active session for '{username}'")
    nas_ip = str(active.nasipaddress)
    nas = db.query(NAS).filter(NAS.nasname == nas_ip).first()
    if not nas:
        raise HTTPException(404, f"NAS '{nas_ip}' not found in nas table")
    success = disconnect_user(nas.nasname, nas.secret, username, active.acctsessionid)
    if not success:
        raise HTTPException(500, f"CoA disconnect failed for '{username}' on {nas.nasname}")
    return {"status": "success", "message": f"User '{username}' disconnected via CoA"}


@router.get("/users/{username}/sessions")
def get_user_sessions(username: str, db: Session = Depends(get_db)):
    sessions = db.query(RadAcct).filter(
        RadAcct.username == username, RadAcct.acctstoptime.is_(None)
    ).order_by(RadAcct.acctstarttime.desc()).all()
    return [_session_dict(s) for s in sessions]


@router.get("/users/{username}/session-history")
def get_session_history(username: str, limit: int = 50, db: Session = Depends(get_db)):
    sessions = db.query(RadAcct).filter(
        RadAcct.username == username
    ).order_by(RadAcct.acctstarttime.desc()).limit(limit).all()
    return [_session_dict(s) for s in sessions]


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
