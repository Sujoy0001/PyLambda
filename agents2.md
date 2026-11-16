# Automated Test Guide

This guide describes how to work with PyLambda's application tests and where
to add coverage for a code change.

## Test layout

- `Tests/test_app.py` is the automated test module for the FastAPI app. It
  uses `unittest.TestCase` and is executed via pytest.
- `Tests/load_test.py` is a separate load-test script for a running application
  and is not part of the automated test suite.

Keep the existing `Tests` directory capitalization when referring to these
files and when running commands.

## How the application tests work

`Tests/test_app.py` sets default environment values for `DATABASE_URL` and
`JWT_SECRET_KEY` before importing the app. The class-level `TestClient` starts
FastAPI's lifespan once for the class and tears it down afterward. The lifespan
initializes the database and connects to Redis, so tests require a reachable
test database and Redis service plus a valid JWT secret. The default database is
SQLite in memory, so use only test resources.

Tests exercise the app through HTTP using `TestClient`; they do not need a
separately running Uvicorn server. Because the main app mounts the API under
`/apps`, auth URLs in the suite look like `/apps/v1/auth/signup`.

The existing coverage includes health checks, CORS, database lifecycle logging,
authentication, password changes and resets, and protected routes. Match that
style: exercise behavior through HTTP and assert both status codes and relevant
response data.

## Add or change a test

1. Identify the behavior and the route, schema, or service it hits.
2. Add a focused test method to `AppTests` in `Tests/test_app.py` for the
   externally observable behavior. Keep the method name descriptive.
3. Send valid and invalid request data through `self.client` and assert the
   expected HTTP status codes and response JSON.
4. Use unique usernames and email addresses when a test creates records. The
   shared test client and in-memory database are reused across methods.
5. Mock external boundaries such as email sending so tests remain repeatable and
   do not contact third-party services.
6. For failures, assert the intended status and ensure the API does not expose
   sensitive information.
7. Run the focused test first, then the full suite if the change affects shared
   startup or auth behavior.

Avoid adding production credentials, depending on live external services, or
using the load-test script as a substitute for correctness tests.

## Run automated tests

From the repository root, run the full suite:

```powershell
uv run python -m pytest
```

Run just the application test module while iterating:

```powershell
uv run python -m pytest Tests/test_app.py -q
```

If startup fails, check that the environment has a valid `JWT_SECRET_KEY`, an
appropriate `DATABASE_URL`, and a reachable Redis service configured by
`REDIS_URL`. Do not point tests at a production database.

## Run the load test separately

Start a test instance first, then run the script from the repository root:

```powershell
uv run python Tests\load_test.py --requests 100 --concurrency 10
```

The script sends requests to a running app, and its database-backed phase
creates test user records that it does not delete. Only use it with an app and
database you control. See `LOAD_TESTING.md` for its options and result
interpretation.
