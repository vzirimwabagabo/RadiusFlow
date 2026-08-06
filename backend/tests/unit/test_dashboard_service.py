import unittest
from datetime import datetime, timezone

from app.schemas.dashboard import DashboardSnapshot, RecentAuthentication
from app.services.dashboard_service import (
    DashboardService,
    PendingSchemaDashboardProvider,
)


class ReadyProvider:
    def fetch_snapshot(self):
        return DashboardSnapshot(
            source_status="ready",
            total_radius_identities=120,
            authentication_attempts=200,
            successful_authentications=180,
            failed_authentications=20,
            authentication_success_rate=90.0,
            online_sessions=21,
            nas_count=3,
            user_group_count=5,
            recent_authentication_activity=[
                RecentAuthentication(
                    username="subscriber-001",
                    occurred_at=datetime(2026, 7, 24, 10, 0, tzinfo=timezone.utc),
                    result="Access-Accept",
                    called_station_id="nas-01",
                )
            ],
        )


class FailingProvider:
    def fetch_snapshot(self):
        raise RuntimeError("database is unavailable")


class DashboardServiceTests(unittest.TestCase):
    def test_pending_provider_does_not_report_unknown_metrics_as_zero(self):
        snapshot = DashboardService(PendingSchemaDashboardProvider()).get_snapshot()

        self.assertEqual(snapshot.source_status, "pending_queries")
        self.assertIsNone(snapshot.total_radius_identities)
        self.assertIsNone(snapshot.online_sessions)
        self.assertEqual(snapshot.recent_authentication_activity, [])
        self.assertEqual(
            {metric.key for metric in snapshot.not_configured},
            {"active_users", "expired_users", "total_vouchers"},
        )

    def test_returns_ready_snapshot_from_injected_provider(self):
        snapshot = DashboardService(ReadyProvider()).get_snapshot()

        self.assertEqual(snapshot.source_status, "ready")
        self.assertEqual(snapshot.total_radius_identities, 120)
        self.assertEqual(snapshot.authentication_success_rate, 90.0)
        self.assertEqual(
            snapshot.recent_authentication_activity[0].username,
            "subscriber-001",
        )

    def test_converts_provider_exception_to_safe_unavailable_snapshot(self):
        snapshot = DashboardService(FailingProvider()).get_snapshot()

        self.assertEqual(snapshot.source_status, "unavailable")
        self.assertIsNone(snapshot.total_radius_identities)
        self.assertEqual(snapshot.recent_authentication_activity, [])


if __name__ == "__main__":
    unittest.main()
