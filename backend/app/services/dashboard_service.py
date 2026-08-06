import logging
from typing import Protocol

from app.schemas.dashboard import DashboardSnapshot

logger = logging.getLogger("radiusflow.dashboard")


class DashboardReadOnlyProvider(Protocol):
    def fetch_snapshot(self) -> DashboardSnapshot:
        """Return dashboard data without modifying source records."""


class PendingSchemaDashboardProvider:
    def fetch_snapshot(self) -> DashboardSnapshot:
        return DashboardSnapshot(
            source_status="pending_queries",
            message=(
                "Production schema validation is complete. Dashboard data remains "
                "disabled until the proposed read-only queries are approved."
            ),
        )


class DashboardService:
    def __init__(self, provider: DashboardReadOnlyProvider):
        self.provider = provider

    def get_snapshot(self) -> DashboardSnapshot:
        try:
            return self.provider.fetch_snapshot()
        except Exception:
            logger.exception("Failed to load dashboard snapshot")
            return DashboardSnapshot(
                source_status="unavailable",
                message="Dashboard data could not be loaded.",
            )


__all__ = [
    "DashboardReadOnlyProvider",
    "DashboardService",
    "PendingSchemaDashboardProvider",
]
