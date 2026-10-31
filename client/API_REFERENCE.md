# PyLambda API Reference

This document describes the HTTP endpoints and JSON schemas currently exposed
by the PyLambda backend.

## Base URL and conventions

Unless configured otherwise, the local development server is available at
`http://127.0.0.1:8000`.

- API versioned endpoints use the `/v1` prefix.
- Request and response bodies use JSON.
- Cross-origin browser requests are enabled. The backend allows all origins by
  default; deployments can restrict this with the `CORS_ORIGINS` JSON array
  setting. Cookie credentials are not enabled.
- Protected endpoints require a bearer access token:

  ```http
  Authorization: Bearer <access_token>
  ```

- Access tokens are issued by `POST /v1/auth/login` and expire after 30 minutes.
- FastAPI validation failures generally return `422 Unprocessable Entity`.
- Error responses use FastAPI's standard shape:

  ```json
  {
    "detail": "Description of the error"
  }
  ```

## Endpoints

### `GET /`

Basic service response. No authentication required.

**Success — `200 OK`**

```json
{
  "message": "the server is working"
}
```

### `GET /health`

Health check. No authentication required.

**Success — `200 OK`**

```json
{
  "status": "ok"
}
```

### `POST /v1/auth/signup`

Creates an account. No authentication required.

**Request body — `Credentials`**

```json
{
  "username": "alex",
  "useremail": "alex@example.com",
  "password": "a-secure-password"
}
```

**Success — `201 Created` — `UserResponse`**

```json
{
  "username": "alex",
  "useremail": "alex@example.com"
}
```

**Notable errors**

- `409 Conflict` — username or email is already registered.
- `422 Unprocessable Entity` — the request does not match the schema.

### `POST /v1/auth/login`

Exchanges an email and password for an access token. No authentication
required.

**Request body — `LoginCredentials`**

```json
{
  "useremail": "alex@example.com",
  "password": "a-secure-password"
}
```

**Success — `200 OK` — `TokenResponse`**

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 1800
}
```

`expires_in` is the token lifetime in seconds.

**Notable errors**

- `401 Unauthorized` — email or password is invalid.
- `422 Unprocessable Entity` — the request does not match the schema.

### `GET /v1/auth/me`

Returns the authenticated user's profile.

**Authentication:** Bearer token required.

**Success — `200 OK` — `UserResponse`**

```json
{
  "username": "alex",
  "useremail": "alex@example.com"
}
```

**Notable errors**

- `401 Unauthorized` — token is missing, invalid, or expired.

### `POST /v1/auth/me/change-password`

Changes the authenticated user's password and invalidates their unused
password-reset tokens.

**Authentication:** Bearer token required.

**Request body — `PasswordChangeRequest`**

```json
{
  "current_password": "current-password",
  "new_password": "new-secure-password"
}
```

**Success — `200 OK`**

```json
{
  "message": "Password changed successfully"
}
```

**Notable errors**

- `400 Bad Request` — the current password is incorrect, or the new password
  is the same as the current password.
- `401 Unauthorized` — token is missing, invalid, or expired.
- `422 Unprocessable Entity` — the request does not match the schema.

### `POST /v1/auth/forgot-password`

Requests a password-reset email. For privacy, the success response is the same
whether or not an account exists for the submitted email. No authentication
required.

**Request body — `ForgotPasswordRequest`**

```json
{
  "useremail": "alex@example.com"
}
```

**Success — `202 Accepted`**

```json
{
  "message": "If the account exists, a password reset email has been sent"
}
```

**Notable errors**

- `503 Service Unavailable` — password-reset email service is not configured
  or the email could not be sent.
- `422 Unprocessable Entity` — the request does not match the schema.

### `POST /v1/auth/reset-password`

Resets a password using the one-time token sent by email. No authentication
required.

**Request body — `ResetPasswordRequest`**

```json
{
  "token": "<token-from-email>",
  "new_password": "new-secure-password"
}
```

**Success — `200 OK`**

```json
{
  "message": "Password reset successfully"
}
```

**Notable errors**

- `400 Bad Request` — reset token is invalid, expired, or already used.
- `422 Unprocessable Entity` — the request does not match the schema.

### `POST /v1/auth/me/verify-phone`

Validates a phone number with the configured phone verification provider and
records the returned phone details for the authenticated user. Only valid
mobile numbers are accepted. A user's existing phone details are updated;
a phone number already linked to another account is rejected.

**Authentication:** Bearer token required.

**Request body — `PhoneVerificationRequest`**

```json
{
  "phone_number": 14155552671
}
```

`phone_number` is an integer in the current backend schema.

**Success — `200 OK`**

```json
{
  "status": "success",
  "message": "Phone registration verified and recorded natively!"
}
```

**Notable errors**

- `400 Bad Request` — number is invalid, is not a mobile line, or is already
  linked to another account.
- `401 Unauthorized` — token is missing, invalid, or expired.
- `503 Service Unavailable` — phone verification provider is unavailable.
- `422 Unprocessable Entity` — the request does not match the schema.

## Schemas

The schemas below describe the backend's current Pydantic models. Fields not
marked optional are required.

### `Credentials`

| Field | Type | Constraints |
| --- | --- | --- |
| `username` | `string` | 3–50 characters |
| `useremail` | `string` | Valid email address; maximum 255 characters |
| `password` | `string` | 8–128 characters |

### `LoginCredentials`

| Field | Type | Constraints |
| --- | --- | --- |
| `useremail` | `string` | Valid email address; maximum 255 characters |
| `password` | `string` | 8–128 characters |

### `PasswordChangeRequest`

| Field | Type | Constraints |
| --- | --- | --- |
| `current_password` | `string` | 8–128 characters |
| `new_password` | `string` | 8–128 characters |

The new password must differ from the current password.

### `ForgotPasswordRequest`

| Field | Type | Constraints |
| --- | --- | --- |
| `useremail` | `string` | Valid email address |

### `ResetPasswordRequest`

| Field | Type | Constraints |
| --- | --- | --- |
| `token` | `string` | 32–256 characters |
| `new_password` | `string` | 8–128 characters |

### `PhoneVerificationRequest`

| Field | Type | Constraints |
| --- | --- | --- |
| `phone_number` | `integer` | Required |

### `TokenResponse`

| Field | Type | Description |
| --- | --- | --- |
| `access_token` | `string` | JWT access token |
| `token_type` | `string` | Always `"bearer"` |
| `expires_in` | `integer` | Token lifetime in seconds (currently `1800`) |

### `UserResponse`

| Field | Type | Description |
| --- | --- | --- |
| `username` | `string` | Account username |
| `useremail` | `string` | Account email address |

## Endpoint summary

| Method | Path | Authentication |
| --- | --- | --- |
| `GET` | `/` | No |
| `GET` | `/health` | No |
| `POST` | `/v1/auth/signup` | No |
| `POST` | `/v1/auth/login` | No |
| `GET` | `/v1/auth/me` | Bearer token |
| `POST` | `/v1/auth/me/change-password` | Bearer token |
| `POST` | `/v1/auth/forgot-password` | No |
| `POST` | `/v1/auth/reset-password` | No |
| `POST` | `/v1/auth/me/verify-phone` | Bearer token |
