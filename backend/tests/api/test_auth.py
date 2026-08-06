import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from auth import create_access_token, verify_token
from app.services.auth_service import AuthService
from database import Base, get_db
from main import app


class AuthSmokeTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)

        db = self.session_factory()
        try:
            AuthService(db).create_user("admin", "Admin-Password-9!", "admin")
        finally:
            db.close()

        def override_db():
            db = self.session_factory()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_db

    def tearDown(self):
        app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_can_create_and_verify_access_token(self):
        token = create_access_token({"sub": "admin"})

        payload = verify_token(token)

        self.assertEqual(payload["sub"], "admin")

    def test_docs_endpoint_is_available(self):
        client = TestClient(app)

        response = client.get("/docs")

        self.assertEqual(response.status_code, 200)
        self.assertIn("RadiusFlow API", response.text)
        self.assertIn("/openapi.json", response.text)

    def test_root_reports_versioned_api_prefix(self):
        client = TestClient(app)

        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["api_prefix"], "/api/v1")

    def test_login_returns_bearer_token(self):
        client = TestClient(app)

        response = client.post(
            "/api/v1/auth/token",
            json={"username": "admin", "password": "Admin-Password-9!"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["token_type"], "bearer")
        token = response.json()["access_token"]
        payload = verify_token(token)
        self.assertEqual(payload["role"], "admin")

        authenticated = client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(authenticated.status_code, 200)

    def test_api_logout_revokes_bearer_token(self):
        client = TestClient(app)
        login = client.post(
            "/api/v1/auth/token",
            json={"username": "admin", "password": "Admin-Password-9!"},
        )
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        logout = client.post("/api/v1/auth/logout", headers=headers)
        after_logout = client.get("/api/v1/users", headers=headers)

        self.assertEqual(logout.status_code, 200)
        self.assertEqual(after_logout.status_code, 401)

    def test_management_routes_require_authentication(self):
        client = TestClient(app)

        response = client.get("/api/v1/users")

        self.assertEqual(response.status_code, 401)



if __name__ == "__main__":
    unittest.main()
