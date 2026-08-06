"""
Milestone 1A — Credential safety: schema-level tests.

These tests run without a database. They verify that the Pydantic response
schemas cannot serialise a RADIUS subscriber password or a NAS shared secret,
regardless of what values are passed in.
"""
import unittest

from schemas import NasResponse, UserResponse


class UserResponsePasswordExclusionTests(unittest.TestCase):
    """UserResponse must not include the subscriber RADIUS password."""

    def _make_response(self, **kwargs) -> dict:
        defaults = {
            "username": "testuser",
            "group_name": "basic",
            "rate_limit": "10M/10M",
            "session_timeout": 3600,
            "max_down": None,
            "max_up": None,
            "idle_timeout": None,
            "expiration": None,
            "status": "active",
        }
        defaults.update(kwargs)
        return UserResponse(**defaults).model_dump()

    def test_password_field_is_not_in_schema(self):
        """UserResponse must have no 'password' field at all."""
        fields = UserResponse.model_fields
        self.assertNotIn(
            "password",
            fields,
            "UserResponse must not define a 'password' field — "
            "the Cleartext-Password must never be serialised into a response.",
        )

    def test_serialised_response_contains_no_password_key(self):
        """model_dump() output must contain no 'password' key."""
        data = self._make_response()
        self.assertNotIn(
            "password",
            data,
            f"Serialised UserResponse must not contain 'password'. Got keys: {list(data.keys())}",
        )

    def test_model_dump_contains_expected_safe_fields(self):
        """Sanity-check: the response must still carry non-sensitive user data."""
        data = self._make_response()
        for field in ("username", "status", "group_name"):
            self.assertIn(field, data)

    def test_cannot_inject_password_via_extra_field(self):
        """Pydantic must not include unexpected 'password' extra fields in the output."""
        res = UserResponse(username="x", status="active", password="leaked")
        self.assertNotIn("password", res.model_dump())


class NasResponseSecretExclusionTests(unittest.TestCase):
    """NasResponse must not include the RADIUS shared secret."""

    def _make_response(self, **kwargs) -> dict:
        defaults = {
            "id": 1,
            "nasname": "192.0.2.1",
            "shortname": "router-01",
            "type": "other",
            "ports": 1812,
            "secret_configured": True,
            "server": None,
            "community": None,
            "description": "Test NAS",
        }
        defaults.update(kwargs)
        return NasResponse(**defaults).model_dump()

    def test_secret_field_is_not_in_schema(self):
        """NasResponse must have no 'secret' field."""
        fields = NasResponse.model_fields
        self.assertNotIn(
            "secret",
            fields,
            "NasResponse must not define a 'secret' field — "
            "the RADIUS shared secret must never be serialised into a response.",
        )

    def test_secret_configured_field_is_present(self):
        """NasResponse must have a boolean 'secret_configured' field instead."""
        fields = NasResponse.model_fields
        self.assertIn(
            "secret_configured",
            fields,
            "NasResponse must define 'secret_configured: bool' as the safe substitute.",
        )

    def test_serialised_response_contains_no_secret_key(self):
        """model_dump() output must contain no 'secret' key."""
        data = self._make_response(secret_configured=True)
        self.assertNotIn(
            "secret",
            data,
            f"Serialised NasResponse must not contain 'secret'. Got keys: {list(data.keys())}",
        )

    def test_secret_configured_true_when_secret_would_be_present(self):
        data = self._make_response(secret_configured=True)
        self.assertTrue(data["secret_configured"])

    def test_secret_configured_false_when_secret_would_be_absent(self):
        data = self._make_response(secret_configured=False)
        self.assertFalse(data["secret_configured"])

    def test_cannot_inject_secret_via_extra_field(self):
        """Pydantic must not include unexpected 'secret' extra fields in the output."""
        res = NasResponse(
            id=1,
            nasname="192.0.2.1",
            shortname="r",
            type="other",
            secret_configured=True,
            secret="supersecretvalue",
        )
        self.assertNotIn("secret", res.model_dump())


if __name__ == "__main__":
    unittest.main()
