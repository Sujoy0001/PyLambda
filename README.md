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
settings. The project reads the environment at startup and expects the
following values to be present:

- `DATABASE_URL` — a SQLAlchemy database URL, such as
  `postgresql+psycopg://user:password@localhost:5432/pylambda`
- `JWT_SECRET_KEY` — a random secret with at least 32 characters
- `REDIS_URL` — the Redis connection string used by the app health checks and
  startup validation
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
  `http://localhost:8000/apps/v1/auth/reset-password`

Reset tokens expire after 15 minutes by default. Change this with
`PASSWORD_RESET_TOKEN_EXPIRE_MINUTES`. Keep SMTP credentials private and never
commit them.

The database and Redis services must be reachable when the application starts.
The database schema is created automatically.

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

Create `.env` from `.env.example` and set `JWT_SECRET_KEY` to a random value
of at least 32 characters. From the project root, build and start the services:

```powershell
docker compose up --build
```

For later runs, start the existing services without rebuilding:

```powershell
docker compose up
```

Use `docker compose up --build` again after changing the Dockerfile or
dependencies.

Compose builds the application image and starts the app, PostgreSQL, and Redis
containers. The app connects to PostgreSQL at `db:5432` and Redis at
`redis:6379` over the Compose network; no external database or Redis URLs are
required. Compose supplies these service URLs to the app, overriding the
corresponding values in `.env`.

PostgreSQL data is stored in a named volume and survives container restarts.
Redis is configured as an ephemeral service, so its data is not persisted.
Default PostgreSQL credentials are for local development only. Set
`POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` to customize them, and
use secure credentials for any non-development deployment.

Stop the services with `Ctrl+C` or run `docker compose down`. To also delete
the persisted PostgreSQL data, run `docker compose down --volumes`.

## API

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | Basic service response |
| `GET` | `/health` | Health check |

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

```RUN
uv run fastapi dev

uv run fastapi run app/main.py --host 0.0.0.0 --port 8000
```