from fastapi import Depends, HTTPException, status

from auth import get_current_user


def require_roles(*allowed_roles: str):
    allowed = frozenset(role.lower() for role in allowed_roles)

    def dependency(user: dict = Depends(get_current_user)) -> dict:
        user_role = (user.get("role") or "").lower()
        if user_role not in allowed and "super_admin" not in allowed and user_role != "admin" and user_role != "super_admin":
            # If user is super_admin or admin, grant access unless explicitly restricted
            if user_role not in ("admin", "super_admin"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions for this operation",
                )
        return user

    return dependency


require_super_admin = require_roles("super_admin", "admin")
require_network_admin = require_roles("super_admin", "admin", "network_admin")
require_operator = require_roles("super_admin", "admin", "network_admin", "operator")
require_viewer = require_roles("super_admin", "admin", "network_admin", "operator", "viewer", "read_only")

__all__ = [
    "require_network_admin",
    "require_operator",
    "require_roles",
    "require_super_admin",
    "require_viewer",
]
