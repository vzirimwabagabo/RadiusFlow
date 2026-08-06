"""Group/package management — radgroupcheck, radgroupreply, radusergroup."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import RadGroupCheck, RadGroupReply, RadUserGroup, RadCheck
from schemas import CreateGroupRequest, GroupResponse

router = APIRouter()


def _build_group_response(db: Session, groupname: str) -> dict:
    replies = db.query(RadGroupReply).filter(RadGroupReply.groupname == groupname).all()
    reply_map = {r.attribute: r.value for r in replies}
    user_count = db.query(RadUserGroup).filter(RadUserGroup.groupname == groupname).count()
    return GroupResponse(
        groupname=groupname,
        rate_limit=reply_map.get("Mikrotik-Rate-Limit"),
        session_timeout=int(reply_map["Session-Timeout"]) if reply_map.get("Session-Timeout") else None,
        max_down=int(reply_map["WISPr-Bandwidth-Max-Down"]) if reply_map.get("WISPr-Bandwidth-Max-Down") else None,
        max_up=int(reply_map["WISPr-Bandwidth-Max-Up"]) if reply_map.get("WISPr-Bandwidth-Max-Up") else None,
        idle_timeout=int(reply_map["Idle-Timeout"]) if reply_map.get("Idle-Timeout") else None,
        user_count=user_count,
    ).model_dump()


@router.get("/groups")
def list_groups(db: Session = Depends(get_db)):
    groupnames = db.query(RadGroupReply.groupname).distinct().all()
    return [_build_group_response(db, g[0]) for g in groupnames]


@router.post("/groups")
def create_group(req: CreateGroupRequest, db: Session = Depends(get_db)):
    existing = db.query(RadGroupReply).filter(RadGroupReply.groupname == req.groupname).first()
    if existing:
        raise HTTPException(409, f"Group '{req.groupname}' already exists")
    if req.rate_limit:
        db.add(RadGroupReply(groupname=req.groupname, attribute="Mikrotik-Rate-Limit", op="=", value=req.rate_limit))
    if req.session_timeout:
        db.add(RadGroupReply(groupname=req.groupname, attribute="Session-Timeout", op="=", value=str(req.session_timeout)))
    if req.max_down:
        db.add(RadGroupReply(groupname=req.groupname, attribute="WISPr-Bandwidth-Max-Down", op="=", value=str(req.max_down)))
    if req.max_up:
        db.add(RadGroupReply(groupname=req.groupname, attribute="WISPr-Bandwidth-Max-Up", op="=", value=str(req.max_up)))
    if req.idle_timeout:
        db.add(RadGroupReply(groupname=req.groupname, attribute="Idle-Timeout", op="=", value=str(req.idle_timeout)))
    if not db.query(RadGroupReply).filter(RadGroupReply.groupname == req.groupname).first():
        db.add(RadGroupReply(groupname=req.groupname, attribute="Idle-Timeout", op="=", value="600"))
    db.commit()
    return _build_group_response(db, req.groupname)


@router.get("/groups/{groupname}")
def get_group(groupname: str, db: Session = Depends(get_db)):
    if not db.query(RadGroupReply).filter(RadGroupReply.groupname == groupname).first():
        raise HTTPException(404, f"Group '{groupname}' not found")
    return _build_group_response(db, groupname)


@router.put("/groups/{groupname}")
def update_group(groupname: str, req: CreateGroupRequest, db: Session = Depends(get_db)):
    if not db.query(RadGroupReply).filter(RadGroupReply.groupname == groupname).first():
        raise HTTPException(404, f"Group '{groupname}' not found")
    db.query(RadGroupReply).filter(RadGroupReply.groupname == groupname).delete()
    if req.rate_limit:
        db.add(RadGroupReply(groupname=groupname, attribute="Mikrotik-Rate-Limit", op="=", value=req.rate_limit))
    if req.session_timeout:
        db.add(RadGroupReply(groupname=groupname, attribute="Session-Timeout", op="=", value=str(req.session_timeout)))
    if req.max_down:
        db.add(RadGroupReply(groupname=groupname, attribute="WISPr-Bandwidth-Max-Down", op="=", value=str(req.max_down)))
    if req.max_up:
        db.add(RadGroupReply(groupname=groupname, attribute="WISPr-Bandwidth-Max-Up", op="=", value=str(req.max_up)))
    if req.idle_timeout:
        db.add(RadGroupReply(groupname=groupname, attribute="Idle-Timeout", op="=", value=str(req.idle_timeout)))
    db.commit()
    return _build_group_response(db, groupname)


@router.delete("/groups/{groupname}")
def delete_group(groupname: str, db: Session = Depends(get_db)):
    if not db.query(RadGroupReply).filter(RadGroupReply.groupname == groupname).first():
        raise HTTPException(404, f"Group '{groupname}' not found")
    db.query(RadGroupReply).filter(RadGroupReply.groupname == groupname).delete()
    db.query(RadGroupCheck).filter(RadGroupCheck.groupname == groupname).delete()
    db.query(RadUserGroup).filter(RadUserGroup.groupname == groupname).delete()
    db.commit()
    return {"status": "success", "message": f"Group '{groupname}' deleted"}


@router.get("/groups/{groupname}/users")
def list_group_users(groupname: str, db: Session = Depends(get_db)):
    mappings = db.query(RadUserGroup).filter(RadUserGroup.groupname == groupname).all()
    return [{"username": m.username, "priority": m.priority} for m in mappings]


@router.post("/groups/{groupname}/users/{username}")
def assign_user(groupname: str, username: str, db: Session = Depends(get_db)):
    if not db.query(RadGroupReply).filter(RadGroupReply.groupname == groupname).first():
        raise HTTPException(404, f"Group '{groupname}' not found")
    existing = db.query(RadUserGroup).filter(RadUserGroup.username == username).first()
    if existing:
        existing.groupname = groupname
    else:
        db.add(RadUserGroup(username=username, groupname=groupname, priority=1))
    db.commit()
    return {"status": "success", "message": f"User '{username}' assigned to '{groupname}'"}


@router.delete("/groups/{groupname}/users/{username}")
def remove_user(groupname: str, username: str, db: Session = Depends(get_db)):
    db.query(RadUserGroup).filter(
        RadUserGroup.username == username, RadUserGroup.groupname == groupname
    ).delete()
    db.commit()
    return {"status": "success", "message": f"User '{username}' removed from '{groupname}'"}