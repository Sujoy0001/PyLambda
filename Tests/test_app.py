import os
import unittest

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault(
    "JWT_SECRET_KEY", "test-only-secret-key-that-is-at-least-32-characters"
)

from main import app


class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)

    def test_root_returns_service_message(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "the server is working"})

    def test_health_returns_ok(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_signup_login_and_protected_profile(self):
        credentials = {"username": "test-user", "password": "correct-horse-battery"}
        signup_response = self.client.post("/v1/auth/signup", json=credentials)
        login_response = self.client.post("/v1/auth/login", json=credentials)

        self.assertEqual(signup_response.status_code, 201)
        self.assertEqual(signup_response.json(), {"username": credentials["username"]})
        self.assertEqual(login_response.status_code, 200)
        token = login_response.json()["access_token"]

        profile_response = self.client.get(
            "/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.json(), {"username": credentials["username"]})

    def test_duplicate_signup_and_invalid_login_are_rejected(self):
        credentials = {"username": "duplicate-user", "password": "correct-horse-battery"}
        self.client.post("/v1/auth/signup", json=credentials)

        duplicate_response = self.client.post("/v1/auth/signup", json=credentials)
        invalid_login_response = self.client.post(
            "/v1/auth/login",
            json={"username": credentials["username"], "password": "wrong-password"},
        )

        self.assertEqual(duplicate_response.status_code, 409)
        self.assertEqual(invalid_login_response.status_code, 401)

    def test_protected_profile_requires_a_valid_token(self):
        response = self.client.get("/v1/auth/me")
        removed_data_route = self.client.get("/v1/data")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(removed_data_route.status_code, 404)


if __name__ == "__main__":
    unittest.main()
