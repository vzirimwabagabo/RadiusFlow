import unittest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from app.models.app.user import AppUser
from app.models.app.audit_log import AuditLog
from app.models.app.voucher import Voucher
from app.repositories.audit_repository import AuditRepository
from app.repositories.voucher_repository import VoucherRepository
from app.services.voucher_service import VoucherService
from app.schemas.voucher import VoucherGenerateRequest, VoucherRedeemRequest


class TestVouchersAndAudit(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()

    def test_audit_repository_record_and_list(self):
        repo = AuditRepository(self.db)
        entry = repo.record(
            action="TEST_ACTION",
            actor="admin",
            resource_type="user",
            resource_id="john_doe",
            details="Created user account",
        )
        self.assertIsNotNone(entry.id)
        self.assertEqual(entry.action, "TEST_ACTION")
        self.assertEqual(entry.actor, "admin")

        logs = repo.list_logs(limit=10)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].action, "TEST_ACTION")

    def test_voucher_repository_batch_generate_and_redeem(self):
        repo = VoucherRepository(self.db)
        vouchers = repo.create_batch(count=5, group_name="10M_Unlimited", created_by="admin")
        self.assertEqual(len(vouchers), 5)
        self.assertTrue(vouchers[0].code.startswith("RF-"))
        self.assertEqual(vouchers[0].status, "unused")

        code_to_redeem = vouchers[0].code
        redeemed = repo.redeem(code_to_redeem, used_by="subscriber_1")
        self.assertIsNotNone(redeemed)
        self.assertEqual(redeemed.status, "used")
        self.assertEqual(redeemed.used_by, "subscriber_1")

        # Double redemption should fail
        fail_redeem = repo.redeem(code_to_redeem, used_by="subscriber_2")
        self.assertIsNone(fail_redeem)

    def test_voucher_service_generate_and_delete(self):
        service = VoucherService(self.db)
        req = VoucherGenerateRequest(count=3, group_name="VIP", expires_in_days=14)
        generated = service.generate_vouchers(req, created_by="manager")
        self.assertEqual(len(generated), 3)

        v_list = service.list_vouchers()
        self.assertEqual(len(v_list), 3)

        code_to_delete = generated[0].code
        success = service.delete_voucher(code_to_delete)
        self.assertTrue(success)

        remaining = service.list_vouchers()
        self.assertEqual(len(remaining), 2)


if __name__ == "__main__":
    unittest.main()
