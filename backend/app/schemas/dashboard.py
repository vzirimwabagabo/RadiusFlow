from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class RecentAuthentication(BaseModel):
    username: str
    occurred_at: datetime | None = None
    result: str | None = None
    called_station_id: str | None = None
    calling_station_id: str | None = None


class UnconfiguredMetric(BaseModel):
    key: Literal["active_users", "expired_users", "total_vouchers"]
    label: str
    reason: str


def _unconfigured_metrics() -> list[UnconfiguredMetric]:
    return [
        UnconfiguredMetric(
            key="active_users",
            label="Active users",
            reason="No production status convention is configured.",
        ),
        UnconfiguredMetric(
            key="expired_users",
            label="Expired users",
            reason="No production expiration convention is configured.",
        ),
        UnconfiguredMetric(
            key="total_vouchers",
            label="Total vouchers",
            reason="No application-owned voucher metadata exists yet.",
        ),
    ]


class RadiusServiceStatus(BaseModel):
    state: Literal["unknown", "online", "offline", "degraded"] = "unknown"
    checked_at: datetime | None = None


class DashboardSnapshot(BaseModel):
    source_status: Literal["pending_queries", "ready", "unavailable"] = (
        "pending_queries"
    )
    total_radius_identities: int | None = None
    authentication_attempts: int | None = None
    successful_authentications: int | None = None
    failed_authentications: int | None = None
    authentication_success_rate: float | None = None
    online_sessions: int | None = None
    nas_count: int | None = None
    user_group_count: int | None = None
    latest_accounting_activity: datetime | None = None
    recent_authentication_activity: list[RecentAuthentication] = Field(
        default_factory=list
    )
    not_configured: list[UnconfiguredMetric] = Field(
        default_factory=_unconfigured_metrics
    )
    radius_service: RadiusServiceStatus = Field(default_factory=RadiusServiceStatus)
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    message: str | None = None
