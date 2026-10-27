import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault(
    "JWT_SECRET_KEY", "test-only-secret-key-that-is-at-least-32-characters"
)


class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app.main import app

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

    def test_database_startup_and_shutdown_are_logged(self):
        from sqlalchemy import create_engine
        from sqlalchemy.schema import MetaData

        from app.middlewares.database_logging import (
            close_database,
            configure_database_connection_logging,
            initialize_database,
        )

        engine = create_engine("sqlite://")
        configure_database_connection_logging(engine)

        with self.assertLogs("fastapi_app", level="INFO") as captured:
            initialize_database(engine, MetaData())
            close_database(engine)

        messages = "\n".join(captured.output)
        for expected_message in (
            "Checking database connection",
            "Database connection established",
            "Database connection is available",
            "Database schema initialized",
            "Closing database connection pool",
            "Database connection closed",
            "Database connection pool closed",
        ):
            with self.subTest(expected_message=expected_message):
                self.assertIn(expected_message, messages)

        self.assertNotIn("acquired from pool", messages)
        self.assertNotIn("returned to pool", messages)

    def test_signup_login_and_protected_profile(self):
        credentials = {
            "username": "test-user",
            "useremail": "test-user@example.com",
            "password": "correct-horse-battery",
        }
        signup_response = self.client.post("/v1/auth/signup", json=credentials)
        login_response = self.client.post("/v1/auth/login", json=credentials)

        self.assertEqual(signup_response.status_code, 201)
        self.assertEqual(
            signup_response.json(),
            {
                "username": credentials["username"],
                "useremail": credentials["useremail"],
            },
        )
        self.assertEqual(login_response.status_code, 200)
        token = login_response.json()["access_token"]

        profile_response = self.client.get(
            "/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(
            profile_response.json(),
            {
                "username": credentials["username"],
                "useremail": credentials["useremail"],
            },
        )

    def test_change_password_requires_authentication_and_password(self):
        credentials = {
            "username": "password-change-user",
            "useremail": "password-change-user@example.com",
            "password": "original-password",
        }
        signup_response = self.client.post("/v1/auth/signup", json=credentials)
        self.assertEqual(signup_response.status_code, 201)

        login_response = self.client.post("/v1/auth/login", json=credentials)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        unauthenticated_response = self.client.post(
            "/v1/auth/me/change-password",
            json={
                "current_password": credentials["password"],
                "new_password": "updated-password",
            },
        )
        self.assertEqual(unauthenticated_response.status_code, 401)

        incorrect_password_response = self.client.post(
            "/v1/auth/me/change-password",
            headers=headers,
            json={
                "current_password": "wrong-password",
                "new_password": "updated-password",
            },
        )
        self.assertEqual(incorrect_password_response.status_code, 400)

        change_response = self.client.post(
            "/v1/auth/me/change-password",
            headers=headers,
            json={
                "current_password": credentials["password"],
                "new_password": "updated-password",
            },
        )
        self.assertEqual(change_response.status_code, 200)

        old_password_login = self.client.post(
            "/v1/auth/login",
            json={
                "useremail": credentials["useremail"],
                "password": credentials["password"],
            },
        )
        new_password_login = self.client.post(
            "/v1/auth/login",
            json={
                "useremail": credentials["useremail"],
                "password": "updated-password",
            },
        )
        self.assertEqual(old_password_login.status_code, 401)
        self.assertEqual(new_password_login.status_code, 200)

    def test_forgot_password_token_resets_password_once(self):
        from app.middlewares.config import settings

        credentials = {
            "username": "forgot-password-user",
            "useremail": "forgot-password-user@example.com",
            "password": "original-password",
        }
        signup_response = self.client.post("/v1/auth/signup", json=credentials)
        self.assertEqual(signup_response.status_code, 201)

        with (
            patch.object(settings, "SMTP_HOST", "smtp.example.com"),
            patch.object(settings, "SMTP_FROM_EMAIL", "noreply@example.com"),
            patch(
                "app.Auth.router.send_password_reset_email"
            ) as send_email,
        ):
            forgot_response = self.client.post(
                "/v1/auth/forgot-password",
                json={"useremail": credentials["useremail"]},
            )

        self.assertEqual(forgot_response.status_code, 202)
        token = send_email.call_args.args[1]

        reset_response = self.client.post(
            "/v1/auth/reset-password",
            json={
                "token": token,
                "new_password": "updated-password",
            },
        )
        self.assertEqual(reset_response.status_code, 200)

        reused_token_response = self.client.post(
            "/v1/auth/reset-password",
            json={
                "token": token,
                "new_password": "another-password",
            },
        )
        self.assertEqual(reused_token_response.status_code, 400)

        old_password_login = self.client.post(
            "/v1/auth/login",
            json={
                "useremail": credentials["useremail"],
                "password": credentials["password"],
            },
        )
        new_password_login = self.client.post(
            "/v1/auth/login",
            json={
                "useremail": credentials["useremail"],
                "password": "updated-password",
            },
        )
        self.assertEqual(old_password_login.status_code, 401)
        self.assertEqual(new_password_login.status_code, 200)

    def test_forgot_password_response_does_not_disclose_unknown_email(self):
        from app.middlewares.config import settings

        with (
            patch.object(settings, "SMTP_HOST", "smtp.example.com"),
            patch.object(settings, "SMTP_FROM_EMAIL", "noreply@example.com"),
            patch(
                "app.Auth.router.send_password_reset_email"
            ) as send_email,
        ):
            response = self.client.post(
                "/v1/auth/forgot-password",
                json={"useremail": "unknown@example.com"},
            )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(
            response.json(),
            {
                "message": (
                    "If the account exists, a password reset email "
                    "has been sent"
                )
            },
        )
        send_email.assert_not_called()

    def test_duplicate_signup_and_invalid_login_are_rejected(self):
        credentials = {
            "username": "duplicate-user",
            "useremail": "duplicate-user@example.com",
            "password": "correct-horse-battery",
        }
        self.client.post("/v1/auth/signup", json=credentials)

        duplicate_response = self.client.post(
            "/v1/auth/signup", json=credentials
        )
        invalid_login_response = self.client.post(
            "/v1/auth/login",
            json={
                "username": credentials["username"],
                "useremail": credentials["useremail"],
                "password": "wrong-password",
            },
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
