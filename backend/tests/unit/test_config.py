import unittest

from pydantic import ValidationError

from config import Settings


class ProductionConfigurationTests(unittest.TestCase):
    def test_rejects_insecure_production_configuration(self):
        with self.assertRaises(ValidationError):
            Settings(
                _env_file=None,
                ENVIRONMENT="production",
                JWT_SECRET="jwt-secret-that-is-long-and-not-default",
                FLASK_SECRET_KEY="flask-secret-that-is-long-and-not-default",
                CORS_ORIGINS=["*"],
                SESSION_COOKIE_SECURE=False,
            )

    def test_accepts_distinct_secrets_https_cookie_and_explicit_origin(self):
        settings = Settings(
            _env_file=None,
            ENVIRONMENT="production",
            JWT_SECRET="jwt-secret-that-is-long-and-not-default",
            FLASK_SECRET_KEY="flask-secret-that-is-long-and-not-default",
            CORS_ORIGINS=["https://radius.example.com"],
            SESSION_COOKIE_SECURE=True,
        )

        self.assertEqual(settings.ENVIRONMENT, "production")
        self.assertEqual(settings.CORS_ORIGINS, ["https://radius.example.com"])
        self.assertTrue(settings.SESSION_COOKIE_SECURE)


if __name__ == "__main__":
    unittest.main()
