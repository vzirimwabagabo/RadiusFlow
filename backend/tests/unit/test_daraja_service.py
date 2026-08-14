import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from app.models.radiusflow.payment import Payment
from app.schemas.payment import STKPushRequest
from app.services.daraja_service import DarajaService, normalize_phone_number


class TestDarajaService(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        self.service = DarajaService(self.db)

    def tearDown(self):
        self.db.close()

    def test_phone_number_normalization(self):
        self.assertEqual(normalize_phone_number("0708374149"), "254708374149")
        self.assertEqual(normalize_phone_number("+254708374149"), "254708374149")
        self.assertEqual(normalize_phone_number("254708374149"), "254708374149")
        self.assertEqual(normalize_phone_number("708374149"), "254708374149")

    @patch("config.settings.DARAJA_CONSUMER_KEY", "mock_key")
    @patch("config.settings.DARAJA_CONSUMER_SECRET", "mock_secret")
    @patch("requests.get")
    @patch("requests.post")
    def test_initiate_stk_push(self, mock_post, mock_get):
        # Mock OAuth token response
        mock_get_resp = MagicMock()
        mock_get_resp.json.return_value = {"access_token": "mock_access_token_123"}
        mock_get_resp.status_code = 200
        mock_get.return_value = mock_get_resp

        # Mock STK push response
        mock_post_resp = MagicMock()
        mock_post_resp.json.return_value = {
            "MerchantRequestID": "29182-100120-1",
            "CheckoutRequestID": "ws_CO_1408202623595912345",
            "ResponseCode": "0",
            "ResponseDescription": "Success. Request accepted for processing",
            "CustomerMessage": "Success. Request accepted for processing",
        }
        mock_post_resp.status_code = 200
        mock_post.return_value = mock_post_resp

        req = STKPushRequest(
            phone_number="0708374149",
            amount=500.0,
            package_name="Monthly-VIP",
        )
        res = self.service.initiate_stk_push(req)

        self.assertEqual(res.merchant_request_id, "29182-100120-1")
        self.assertEqual(res.checkout_request_id, "ws_CO_1408202623595912345")

        # Verify DB record created with status PENDING
        payment = self.db.query(Payment).filter_by(checkout_request_id="ws_CO_1408202623595912345").first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, "PENDING")
        self.assertEqual(payment.phone_number, "254708374149")
        self.assertEqual(float(payment.amount), 500.0)

    def test_process_callback_success(self):
        # Seed pending payment
        p = Payment(
            merchant_request_id="M123",
            checkout_request_id="ws_CO_TEST_SUCCESS",
            phone_number="254708374149",
            amount=100.0,
            status="PENDING",
        )
        self.db.add(p)
        self.db.commit()

        payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "M123",
                    "CheckoutRequestID": "ws_CO_TEST_SUCCESS",
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 100.0},
                            {"Name": "MpesaReceiptNumber", "Value": "QKH789XYZ"},
                            {"Name": "TransactionDate", "Value": 20260814231500},
                            {"Name": "PhoneNumber", "Value": 254708374149},
                        ]
                    },
                }
            }
        }

        updated = self.service.process_callback(payload)
        self.assertIsNotNone(updated)
        self.assertEqual(updated.status, "SUCCESS")
        self.assertEqual(updated.mpesa_receipt_number, "QKH789XYZ")
        self.assertEqual(updated.result_code, 0)

    def test_process_callback_cancelled_by_user(self):
        p = Payment(
            merchant_request_id="M124",
            checkout_request_id="ws_CO_TEST_CANCEL",
            phone_number="254708374149",
            amount=100.0,
            status="PENDING",
        )
        self.db.add(p)
        self.db.commit()

        payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "M124",
                    "CheckoutRequestID": "ws_CO_TEST_CANCEL",
                    "ResultCode": 1032,
                    "ResultDesc": "Request cancelled by user",
                }
            }
        }

        updated = self.service.process_callback(payload)
        self.assertIsNotNone(updated)
        self.assertEqual(updated.status, "CANCELLED")
        self.assertEqual(updated.result_code, 1032)


if __name__ == "__main__":
    unittest.main()
