from dataclasses import dataclass


@dataclass
class Package:
    name: str
    rate_limit: str | None = None
    validity_days: int | None = None
