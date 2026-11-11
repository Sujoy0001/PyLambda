# Automated Test Guide

This guide describes how to work with PyLambda's application tests and where
to add coverage for a code change.

## Test layout

- `Tests/test_app.py` is the current automated test module. It uses
  `unittest.TestCase` and is run by pytest.
- `Tests/load_test.py` is a command-line load-test script for a running
  application. It creates user records during its database phase and is not
  part of the automated test suite.

Keep the existing `Tests` directory capitalization when referring to these
files and running commands.

## How the application tests work

`Tests/test_app.py` sets default test environment values for `DATABASE_URL`
and `JWT_SECRET_KEY` before importing the application. Its class-level
`TestClient` context starts the FastAPI lifespan once for the class and closes
it afterward. The lifespan initializes the database and connects to Redis, so
tests need a reachable test database and Redis service, along with a valid JWT
secret. The database default is in-memory SQLite; use only test resources.

Tests make requests to the in-process app using `TestClient`; they do not need
a separately running Uvicorn server. The API router includes the `/apps`
prefix, so authentication URLs in these tests look like
`/apps/v1/auth/signup`.

The existing tests cover service health, CORS, database lifecycle logging,
authentication, password changes and resets, and protected routes. Match
their style: exercise behavior through HTTP where possible and assert both
status codes and relevant response data.

## Add or change a test

1. Identify the behavior and its route, schema, or service in the application.
2. Add a focused test method to `AppTests` in `Tests/test_app.py` for
   externally observable behavior. Keep the test name descriptive.
3. Send valid and invalid request data through `self.client`; assert expected
   status codes and response JSON.
4. Use unique usernames and email addresses when a test creates database
   records. The test client and in-memory database are shared across methods
   in the test class.
5. Mock external boundaries (for example email sending or phone verification)
   so tests are repeatable and do not contact third-party services.
6. For errors, assert the intended failure status and ensure the behavior does
   not disclose sensitive information.
7. Run the focused test, then run the full suite if shared application
   behavior or startup code changed.

Avoid adding production credentials, depending on a live external service,
or using the load-test script as a substitute for correctness tests.

## Run automated tests

From the repository root, run the full suite:

```powershell
uv run python -m pytest
```

Run just the application test module while iterating:

```powershell
uv run python -m pytest Tests/test_app.py -q
```

If startup fails, check that the test environment has a valid `JWT_SECRET_KEY`,
an appropriate `DATABASE_URL`, and a reachable Redis service configured by
`REDIS_URL`. Do not point tests at a production database.

## Run the load test separately

Start a test instance first, then run the script from the repository root:

```powershell
uv run python Tests\load_test.py --requests 100 --concurrency 10
```

The script sends requests to a running app and its database-backed phase
creates test user records that it does not delete. Only use it with an app
and database you control. See `LOAD_TESTING.md` for its options and results.
