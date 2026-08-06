from dataclasses import dataclass


@dataclass
class Voucher:
    code: str
    username: str | None = None
    status: str = "unused"
