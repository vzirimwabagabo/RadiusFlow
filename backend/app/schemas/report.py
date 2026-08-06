from pydantic import BaseModel


class ReportSummary(BaseModel):
    name: str
    total: int = 0
