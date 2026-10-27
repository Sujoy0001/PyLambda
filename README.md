# PyLambda

PyLambda is a FastAPI service with username/password authentication, JWT bearer
tokens, and SQLAlchemy-backed user storage.

## Requirements

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL for a persistent database (SQLite URLs are also supported)

## Setup

Install the project dependencies:

```powershell
uv sync
```

Copy `.env.example` to `.env`, then replace the example values with your
settings:

- `DATABASE_URL` — a SQLAlchemy database URL, such as
  `postgresql+psycopg://user:password@localhost:5432/pylambda`
- `JWT_SECRET_KEY` — a random secret with at least 32 characters
- `CORS_ORIGINS` — JSON array of allowed browser origins; defaults to `["*"]`.
  For production, set this to your frontend origin(s), for example
  `["https://example.com"]`.

For password-reset emails, configure the SMTP values in `.env`. The example
uses Gmail's SMTP host; for Gmail, `SMTP_PASSWORD` must be a Google App
Password (not your normal Gmail password). Other providers require their own
SMTP host, port, and credentials.

- `SMTP_HOST` — SMTP server hostname
- `SMTP_PORT` — SMTP port (defaults to `587`)
- `SMTP_USERNAME` and `SMTP_PASSWORD` — optional SMTP authentication
- `SMTP_FROM_EMAIL` — sender email address
- `SMTP_USE_TLS` — use STARTTLS (defaults to `true`)
- `PASSWORD_RESET_API_URL` — API URL included in reset emails; defaults to
  `http://localhost:8000/v1/auth/reset-password`

Reset tokens expire after 15 minutes by default. Change this with
`PASSWORD_RESET_TOKEN_EXPIRE_MINUTES`. Keep SMTP credentials private and never
commit them.

The database must be reachable when the application starts. Its tables are
created automatically.

Logs are written to the console and `Logs/app.log`.

At startup, the app verifies the database connection and logs whether it is
available before initializing the schema. At shutdown, it closes the database
connection pool. Database connection lifecycle messages are written to the
console and `Logs/app.log`; normal per-request pool activity is not logged.

## Run

Start the development server from the project root:

```powershell
uv run uvicorn app.main:app --reload
```

The interactive API documentation is available at
<http://127.0.0.1:8000/docs>.

The API enables CORS for browser-based clients. By default any origin is
allowed and cookies are not enabled. Restrict `CORS_ORIGINS` in `.env` to your
frontend's origin(s) when deploying.

## Run with Docker

After configuring `.env` as described above, build and start the app from the
project root:

```powershell
docker compose up --build
```

Compose loads `.env` into the container at runtime. The file is not copied into
the image. Stop the app with `Ctrl+C`, or run `docker compose down` in another
terminal.

The database must be reachable from inside the container. When connecting to a
database running directly on the host, use `host.docker.internal` instead of
`localhost` in `DATABASE_URL`.

## API

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | Basic service response |
| `GET` | `/health` | Health check |
| `POST` | `/v1/auth/signup` | Register with a username and password |
| `POST` | `/v1/auth/login` | Exchange credentials for an access token |
| `GET` | `/v1/auth/me` | Get the authenticated user's profile |
| `POST` | `/v1/auth/me/change-password` | Change password for the authenticated user |
| `POST` | `/v1/auth/forgot-password` | Request a password reset email |
| `POST` | `/v1/auth/reset-password` | Reset password with an emailed token |

To request a reset, send `POST /v1/auth/forgot-password` with:

```json
{
  "useremail": "you@example.com"
}
```

The email contains a one-time token. Submit it with the new password to
`POST /v1/auth/reset-password`:

```json
{
  "token": "token-from-the-email",
  "new_password": "your-new-password"
}
```

Signup and login accept JSON with a `username` (3–50 characters) and `password`
(8–128 characters). Send the login response's `access_token` on protected
requests using the `Authorization: Bearer <token>` header. Access tokens expire
after 30 minutes.

## Tests

Run the test suite with:

```powershell
uv run python -m pytest
```

## Load test

See [LOAD_TESTING.md](./LOAD_TESTING.md) for instructions on running the
automated tests and load test, configuring the target app, and understanding
the results.

Quick start: start the app, then run:

```powershell
uv run python Tests\load_test.py --requests 100 --concurrency 10
```
