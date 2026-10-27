# Testing and Load Testing

This guide covers the automated test suite and the load-test script.

## Run the automated tests

From the project root, run:

```powershell
uv run python -m pytest
```

These tests verify application routes, authentication behavior, and database
connection lifecycle logging. They use SQLite configured by the test module
and do not require a separate running server.

## Prepare for a load test

The load test sends requests to a running instance of the app. Configure
`.env` with a database URL and JWT secret, then start the app in one terminal:

```powershell
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Keep the server running. In a second terminal, run the load-test script from
the project root.

> **Use a test database.** The database phase calls the signup endpoint and
> creates a new user record for every successful request. The script does not
> delete those records afterward. Only run it against an application and
> database you control.

## Run the load test

Run 100 requests per phase with up to 10 requests in flight at a time:

```powershell
uv run python Tests\load_test.py --requests 100 --concurrency 10
```

By default, the script targets `http://127.0.0.1:8000`. To target another
running instance, provide its base URL:

```powershell
uv run python Tests\load_test.py `
  --base-url http://127.0.0.1:8000 `
  --requests 200 `
  --concurrency 20
```

The two options control:

- `--requests`: total requests sent in **each** phase.
- `--concurrency`: maximum number of requests sent at the same time. It must
  be positive and no greater than `--requests`.
- `--base-url`: address of the running app.

Start with modest values and increase them gradually. Higher concurrency may
overload the app or database; this script does not automatically determine a
safe production capacity.

## What is measured

The script runs two phases:

1. **Application check:** sends `GET /health`. This measures basic HTTP
   handling and does not query the database.
2. **Database-backed check:** sends `POST /v1/auth/signup` with a unique test
   username. This exercises request handling, password hashing, and a database
   write. It measures the complete signup operation, not database performance
   in isolation.

For each phase, the script prints:

- **Requests / Successful / Failed:** number of calls and how many received
  the expected HTTP status (`200` for health and `201` for signup).
- **HTTP statuses:** counts grouped by response status.
- **Elapsed:** total time for that phase.
- **Throughput:** total requests divided by elapsed time, in requests per
  second.
- **Latency avg / p95 / max:** average, 95th-percentile, and slowest individual
  request time in milliseconds.
- **Errors:** a summary when calls fail or return an unexpected status.

The script exits with status `0` if all calls succeed in both phases, and
status `1` if any call fails.

## Stop the server

When the load test is finished, return to the server terminal and press
`Ctrl+C`.
