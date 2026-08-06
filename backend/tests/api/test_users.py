import unittest

from fastapi.testclient import TestClient

from app.main import app as package_app
from main import app


class UserRouteSmokeTests(unittest.TestCase):
    def test_openapi_contains_user_routes(self):
        client = TestClient(app)

        response = client.get("/openapi.json")

        self.assertEqual(response.status_code, 200)
        paths = response.json()["paths"]
        self.assertIn("/api/v1/users", paths)
        self.assertIn("/api/v1/users/expired", paths)
        self.assertIn("/api/v1/users/expiring-soon", paths)
        self.assertIn("/api/v1/users/{username}", paths)
        self.assertIn("/api/v1/users/{username}/disconnect", paths)
        self.assertIn("/api/v1/auth/token", paths)
        self.assertNotIn("/users", paths)

    def test_package_entrypoint_exposes_same_app(self):
        client = TestClient(package_app)

        response = client.get("/openapi.json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("/api/v1/users", response.json()["paths"])

    def test_legacy_routes_still_exist_but_are_hidden_from_swagger(self):
        client = TestClient(app)

        route_paths = {route.path for route in app.routes}
        openapi_paths = client.get("/openapi.json").json()["paths"]

        self.assertIn("/users", route_paths)
        self.assertIn("/api/v1/users", route_paths)
        self.assertNotIn("/users", openapi_paths)


if __name__ == "__main__":
    unittest.main()
