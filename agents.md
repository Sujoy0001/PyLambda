# AI Agent Guide

This guide explains where to start when changing PyLambda and how to keep
changes consistent with the existing FastAPI project.

## Start here

1. Read `README.md` for the app setup, required environment variables, and the
   public API surface.
2. Read `pyproject.toml` for supported Python and project dependencies.
3. Follow the route imports and router structure before adding new code; do not
   create a parallel implementation that bypasses the current app layout.
4. Read `agents2.md` before changing or adding automated tests.

PyLambda is a Python 3.11+ FastAPI application using SQLAlchemy, Redis, and
JWT-based auth. Use `uv` for dependency and test commands.

## Application map

- `app/main.py` builds the FastAPI app, configures CORS and request logging,
  starts Redis, and initializes the database lifecycle.
- `app/Api/v1/router.py` mounts the v1 auth router under `/v1`.
- `app/Api/v2/router.py` mounts the webhook router under `/v2`.
- `app/Auth/router.py` implements signup, login, profile lookup, password change,
  and password-reset flows.
- `app/Auth/schemas.py` defines the request and response models used by auth
  endpoints.
- `app/Auth/security.py` contains password hashing, JWT creation/validation, and
  token helpers.
- `app/db/session.py` owns the database engine, lifecycle hooks, and `get_db`.
- `app/config.py` defines environment-backed settings and defaults.
- `app/models/` contains the SQLAlchemy models and webhook record table.
- `Tests/test_app.py` holds the automated tests for the app.
- `Tests/load_test.py` is a separate load-test script and is not a unit test.

The application exposes API routes under the `/apps` prefix through the main
router:

- `/apps/v1/auth/...`
- `/apps/v2/github-webhook`

Check the router definitions before adding endpoints; do not assume paths from
external examples or omit the `/apps` prefix.

## Implement a change step by step

1. **Find the owning layer.** Start at the route that exposes the behavior,
   then follow the schema, model, and dependency used by it.
2. **Define API data shapes.** Add or update Pydantic request/response models in
   the relevant schema module. Keep validation explicit.
3. **Update persistence only when needed.** Put SQLAlchemy model changes in the
   owning model module and keep database work in the shared `get_db` flow.
4. **Implement route behavior.** Use the existing router patterns and raise
   `HTTPException` for expected errors instead of swallowing failures.
5. **Keep startup/config behavior consistent.** Any env-backed configuration or
   Redis/database initialization change should still pass application startup.
6. **Register routes if necessary.** New routers must be included in the app's
   router hierarchy so they receive the `/apps` prefix when applicable.
7. **Add or update focused tests.** Follow `agents2.md`; test actual HTTP
   behavior and assert both status codes and response data.
8. **Run the relevant checks.** Start with the focused test file, then run the
   full suite if the change affects shared startup or auth behavior.
9. **Update documentation** when public API behavior, configuration, or setup
   changes.

## Repository conventions and guardrails

- Preserve the existing package capitalization (`app/Api`, `app/Auth`,
  `Tests`) and import paths.
- Reuse existing settings and helpers instead of duplicating logic.
- Do not put database queries, secrets, or credentials in route handlers or
  tests unnecessarily.
- Tests must not call real email or phone-verification services; mock those
  boundaries.
- Do not commit `.env` values, credentials, or other secrets. Use environment
  settings for configuration.
- Keep changes limited to the requested behavior and preserve existing API
  responses unless a change explicitly requires a different contract.
