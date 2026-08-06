"""NAS device management — nas table."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import NAS, RadAcct
from schemas import CreateNASRequest

router = APIRouter()


@router.get("/nas")
def list_nas(db: Session = Depends(get_db)):
    devices = db.query(NAS).order_by(NAS.nasname).all()
    return [_nas_dict(d) for d in devices]


@router.post("/nas")
def create_nas(req: CreateNASRequest, db: Session = Depends(get_db)):
    if db.query(NAS).filter(NAS.nasname == req.nasname).first():
        raise HTTPException(409, f"NAS '{req.nasname}' already exists")
    nas = NAS(
        nasname=req.nasname, shortname=req.shortname, type=req.type,
        secret=req.secret, ports=req.ports, server=req.server,
        community=req.community, description=req.description,
    )
    db.add(nas)
    db.commit()
    db.refresh(nas)
    return _nas_dict(nas)


@router.get("/nas/{ip}")
def get_nas(ip: str, db: Session = Depends(get_db)):
    nas = db.query(NAS).filter(NAS.nasname == ip).first()
    if not nas:
        raise HTTPException(404, f"NAS '{ip}' not found")
    return _nas_dict(nas)


@router.put("/nas/{ip}")
def update_nas(ip: str, req: CreateNASRequest, db: Session = Depends(get_db)):
    nas = db.query(NAS).filter(NAS.nasname == ip).first()
    if not nas:
        raise HTTPException(404, f"NAS '{ip}' not found")
    nas.shortname = req.shortname or nas.shortname
    nas.type = req.type or nas.type
    nas.secret = req.secret or nas.secret
    nas.ports = req.ports or nas.ports
    nas.server = req.server or nas.server
    nas.community = req.community or nas.community
    nas.description = req.description or nas.description
    db.commit()
    return _nas_dict(nas)


@router.delete("/nas/{ip}")
def delete_nas(ip: str, db: Session = Depends(get_db)):
    nas = db.query(NAS).filter(NAS.nasname == ip).first()
    if not nas:
        raise HTTPException(404, f"NAS '{ip}' not found")
    db.delete(nas)
    db.commit()
    return {"status": "success", "message": f"NAS '{ip}' deleted"}


@router.get("/nas/sessions/active")
def active_sessions_per_nas(db: Session = Depends(get_db)):
    sessions = db.query(RadAcct).filter(RadAcct.acctstoptime.is_(None)).all()
    by_nas = {}
    for s in sessions:
        nas_ip = str(s.nasipaddress)
        by_nas[nas_ip] = by_nas.get(nas_ip, 0) + 1
    return by_nas


def _nas_dict(d: NAS) -> dict:
    return {
        "id": d.id, "nasname": d.nasname, "shortname": d.shortname,
        "type": d.type,
        # secret is intentionally excluded — the RADIUS shared secret must never leave the server.
        "secret_configured": bool(d.secret),
        "ports": d.ports,
        "server": d.server, "community": d.community, "description": d.description,
    }
