from datetime import datetime


def format_radius_expiration(dt: datetime) -> str:
    return dt.strftime("%d %b %Y %H:%M:%S")
