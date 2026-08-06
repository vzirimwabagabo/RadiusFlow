from pydantic import BaseModel


class VoucherResponse(BaseModel):
    code: str
    username: str | None = None
    status: str = "unused"
