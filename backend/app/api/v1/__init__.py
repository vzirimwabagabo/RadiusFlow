from fastapi import APIRouter

from app.api.v1.endpoints import (
    accounting,
    auth,
    coa,
    dashboard,
    nas,
    notifications,
    packages,
    reports,
    sessions,
    system,
    users,
    vouchers,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(packages.router)
api_router.include_router(vouchers.router)
api_router.include_router(nas.router)
api_router.include_router(sessions.router)
api_router.include_router(accounting.router)
api_router.include_router(coa.router)
api_router.include_router(dashboard.router)
api_router.include_router(reports.router)
api_router.include_router(notifications.router)
api_router.include_router(system.router)

__all__ = ["api_router"]
