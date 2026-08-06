"""
Milestone 1A — Security regression integration tests.

These tests use an in-memory SQLite database and FastAPI TestClient
to verify that:
1. GET /api/v1/users does NOT return subscriber passwords.
2. GET /api/v1/nas does NOT return RADIUS shared secrets (returns secret_configured=True/False).
3. The server startup / login flow does NOT automatically create admin users.
"""
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from models import RadCheck, NAS
from main import app
from app.services.auth_service import AuthService
from auth import create_access_token


class SecurityRegressionApiTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)

        # Populate test database
        db = self.session_factory()
        try:
            # Create test admin user explicitly
            service = AuthService(db)
            service.create_user("admin", "Admin-Password-9!", "admin")
            
            # Create a subscriber with Cleartext-Password in radcheck
            db.add(RadCheck(username="subscriber1", attribute="Cleartext-Password", op=":=", value="SecretSubscriberPass123!"))
            
            # Create a NAS device with shared secret
            db.add(NAS(nasname="10.0.0.1", shortname="main-router", secret="SuperSecretRadiusKey456!", type="mikrotik"))
            db.commit()
        finally:
            db.close()

        def override_db():
            db = self.session_factory()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)

        # Login to obtain a valid JWT token backed by an AppSession
        login_res = self.client.post(
            "/api/v1/auth/token",
            json={"username": "admin", "password": "Admin-Password-9!"},
        )
        self.token = login_res.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def tearDown(self):
        app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_users_endpoint_does_not_leak_passwords(self):
        """GET /api/v1/users must never return Cleartext-Password."""
        response = self.client.get("/api/v1/users", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data), 0)
        
        user_entry = next(u for u in data if u["username"] == "subscriber1")
        self.assertNotIn("password", user_entry)
        self.assertNotIn("SecretSubscriberPass123!", str(response.json()))

    def test_single_user_endpoint_does_not_leak_password(self):
        """GET /api/v1/users/{username} must never return Cleartext-Password."""
        response = self.client.get("/api/v1/users/subscriber1", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotIn("password", data)
        self.assertNotIn("SecretSubscriberPass123!", response.text)

    def test_nas_endpoint_does_not_leak_secrets(self):
        """GET /api/v1/nas must return secret_configured: True, but NOT the secret value."""
        response = self.client.get("/api/v1/nas", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data), 0)

        nas_entry = next(n for n in data if n["nasname"] == "10.0.0.1")
        self.assertNotIn("secret", nas_entry)
        self.assertIn("secret_configured", nas_entry)
        self.assertTrue(nas_entry["secret_configured"])
        self.assertNotIn("SuperSecretRadiusKey456!", response.text)

    def test_single_nas_endpoint_does_not_leak_secret(self):
        """GET /api/v1/nas/{ip} must return secret_configured: True, but NOT the secret value."""
        response = self.client.get("/api/v1/nas/10.0.0.1", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotIn("secret", data)
        self.assertIn("secret_configured", data)
        self.assertTrue(data["secret_configured"])
        self.assertNotIn("SuperSecretRadiusKey456!", response.text)

    def test_login_does_not_auto_create_non_existent_admin(self):
        """POST /api/v1/auth/token for unknown user must fail and not create the user."""
        response = self.client.post(
            "/api/v1/auth/token",
            json={"username": "nonexistent_admin", "password": "Admin-Password-9!"},
        )
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
