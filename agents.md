# AI Agent Guide

This guide explains where to start when changing PyLambda and how to keep
changes consistent with the existing application.

## Start here

1. Read `README.md` for setup, configuration, and user-facing API behavior.
2. Read `pyproject.toml` for the supported Python version and dependencies.
3. Find the existing route and follow its imports before deciding where to
   make a change. Avoid creating a parallel implementation.
4. Read `agents2.md` before changing or adding automated tests.

PyLambda is a Python 3.11+ FastAPI application. Use `uv` for project
dependencies and commands.

## Application map

- `app/main.py` creates the FastAPI app, configures middleware, provides the
  root and health endpoints, and manages database and Redis startup/shutdown.
- `app/Api/router.py` assembles API routers under the `/apps` prefix.
- `app/Api/v1/auth_routes.py` mounts the auth router at `/v1/auth`.
- `app/Auth/router.py` implements authentication, password reset, and phone
  verification endpoints. `app/Auth/schemas.py` defines their request and
  response models; `app/Auth/security.py` handles password and JWT helpers.
- `app/Api/v1/product_routes.py` exposes database-backed product reads.
- `app/Api/v2/product_routes.py` exposes product reads and creation with Redis
  caching. `app/redis/product_cache.py` owns cache keys, TTLs, and invalidation.
- `app/services/product_service.py` contains product database operations.
- `app/models/` and `app/Auth/models.py` contain SQLAlchemy models.
- `app/schemas/` and `app/Auth/schemas.py` contain Pydantic API schemas.
- `app/db/session.py` provides the database engine, lifecycle, and `get_db`
  dependency.
- `app/config.py` defines application settings.
- `Tests/test_app.py` contains automated application tests.
- `Tests/load_test.py` is a separate script for exercising a running service;
  it is not a unit or integration test.

The current assembled product and authentication routes include `/apps`:

- `/apps/v1/auth/...`
- `/apps/v1/products`
- `/apps/v2/products`

Check the router definitions when adding endpoints; do not assume paths from
external examples or omit the `/apps` prefix.

## Implement a change step by step

1. **Find the owning layer.** Start at the route for an API behavior, then
   follow its schema, service, model, and dependencies as applicable.
2. **Define API data shapes.** Add or update Pydantic request/response models
   in the relevant schema module. Keep input validation and response shape
   explicit.
3. **Update persistence only when needed.** Put SQLAlchemy model changes in
   the owning model module. Keep database operations in the relevant service
   or existing domain module, and use the shared `get_db` dependency for
   request-scoped sessions.
4. **Implement route behavior.** Use the existing router and dependency
   patterns. Return appropriate HTTP status codes and raise
   `HTTPException` for expected API errors rather than hiding failures.
5. **Preserve cache behavior.** Product v2 routes use Redis; when changing
   product data, consider both the individual product key and cached product
   lists. Use helpers in `app/redis/product_cache.py`.
6. **Register routes if necessary.** A new router must be included through the
   existing API router hierarchy so it receives the `/apps` prefix.
7. **Add or update focused tests.** Follow `agents2.md`; test observable
   status codes, response bodies, and relevant failure cases.
8. **Run the relevant checks.** Start with the focused test file, then run the
   complete test suite for changes that affect shared behavior.
9. **Update documentation** when public API behavior, configuration, setup,
   or commands change.

## Repository conventions and guardrails

- Preserve the existing package capitalization (`app/Api` and `app/Auth`);
  imports are case-sensitive on many deployment systems.
- Reuse existing settings, dependencies, and helpers rather than duplicating
  them.
- Do not put database queries, secrets, or external service credentials in
  route handlers or tests unnecessarily.
- Tests must not call real email or phone-verification services. Mock those
  boundaries in tests.
- Do not commit `.env` values, credentials, or other secrets. Use environment
  settings for configuration.
- Keep changes limited to the requested behavior and preserve existing API
  response shapes unless a change explicitly requires otherwise.
