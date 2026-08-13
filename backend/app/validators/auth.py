import re


ALLOWED_ROLES = frozenset({"super_admin", "admin", "network_admin", "operator", "viewer"})
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{2,63}$")


def normalize_username(username: str) -> str:
    normalized = (username or "").strip().lower()
    if not USERNAME_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Username must be 3-64 characters and use only letters, numbers, dots, "
            "underscores, or hyphens."
        )
    return normalized


def validate_password(password: str) -> str:
    if not 12 <= len(password or "") <= 128:
        raise ValueError("Password must be between 12 and 128 characters.")

    character_groups = (
        any(char.islower() for char in password),
        any(char.isupper() for char in password),
        any(char.isdigit() for char in password),
        any(not char.isalnum() for char in password),
    )
    if sum(character_groups) < 3:
        raise ValueError(
            "Password must contain characters from at least three of these groups: "
            "lowercase, uppercase, numbers, and symbols."
        )
    return password


def validate_role(role: str) -> str:
    normalized = (role or "").strip().lower()
    if normalized not in ALLOWED_ROLES:
        raise ValueError(f"Role must be one of: {', '.join(sorted(ALLOWED_ROLES))}.")
    return normalized
