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

Copy `.env.example` to `.env`, then configure:

- `DATABASE_URL` — a SQLAlchemy database URL, such as
  `postgresql+psycopg://user:password@localhost:5432/pylambda`
- `JWT_SECRET_KEY` — a random secret with at least 32 characters

The database must be reachable when the application starts. Its tables are
created automatically.

## Run

Start the development server from the project root:

```powershell
uv run uvicorn app.main:app --reload
```

The interactive API documentation is available at
<http://127.0.0.1:8000/docs>.

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

Signup and login accept JSON with a `username` (3–50 characters) and `password`
(8–128 characters). Send the login response's `access_token` on protected
requests using the `Authorization: Bearer <token>` header. Access tokens expire
after 30 minutes.

## Tests

Run the test suite with:

```powershell
uv run python -m pytest
```
