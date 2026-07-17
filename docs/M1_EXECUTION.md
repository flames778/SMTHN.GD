# M1 Execution Log

Date started: 2026-07-17
Status: In progress

## Slice 1: Actor Context and Consent Use Case

Completed:

- Created the canonical Python package in `apps/backend/lockdin_backend`.
- Added immutable `ActorContext` with user, device, and session identity.
- Added a FastAPI header dependency that rejects missing actor identity with a problem-details payload.
- Removed all `MVP_USER_ID` and `local-user` identity invention from API routes and workers.
- Changed Google sync task dispatch to carry `user_id` across the Celery boundary.
- Migrated consent upsert into an application use case with repository and unit-of-work ports.
- Replaced deprecated FastAPI startup events with lifespan management.
- Added the canonical backend to Python packaging, tests, linting, typing, and coverage CI gates.
- Created and validated a Python 3.11 local environment in `venv/`.

Validation:

- Canonical identity and consent tests pass under Python 3.11.
- Protected legacy routes return 401 when actor context is absent.
- Combined canonical and migration-source test suite passes: 13 tests.
- Strict mypy and Ruff gates pass for canonical code and owned automation scripts.
- Measured combined coverage is 63.24%; CI floor is ratcheted to the M1 target of 45%.

## Slice 2: Identity Persistence and Authenticated Sessions

Completed:

- Added users, devices, sessions, and conversations to canonical persistence.
- Added Alembic migration `0003_identity_and_conversations`.
- Replaced caller-supplied identity headers with opaque `X-Lockdin-Session-Token` resolution.
- Store only SHA-256 session-token digests; the raw token is returned once at issuance.
- Enforce session expiry, revocation, active-user status, and actor ownership.
- Added a setup-secret-gated, one-time owner bootstrap endpoint.
- Added a database uniqueness constraint to prevent concurrent duplicate owner bootstrap.

Validation:

- Combined canonical and migration-source suite passes: 20 tests.
- Measured combined coverage is 69.81% against the 45% CI floor.
- Alembic offline PostgreSQL generation emits all four identity tables through `head`.
- Ruff and strict mypy gates pass.

## Security Boundary

Protected routes now accept only an opaque session token and resolve actor identity from persistence. The one-time bootstrap route requires a separate `APP_BOOTSTRAP_TOKEN` of at least 32 characters. Session tokens are high-entropy values stored only as SHA-256 digests. Remote exposure still requires the M3 authenticated local-host boundary and request hardening from M1-T08.

## Slice 3: Encrypted Integration Credentials at Rest

Completed:

- Created `TokenEncryption` service using Fernet (AES-128-CBC + HMAC-SHA256).
- Encrypted tokens automatically on write via `IntegrationRepository.upsert_google()`, `update_tokens()`, and `revoke()`.
- Decryption abstracted to `get_decrypted_tokens()` for transparent token retrieval.
- Updated API routes to decrypt tokens before passing to OAuth service (refresh endpoint).
- Updated sync worker to decrypt tokens before passing to integration sync service.
- Created comprehensive tests: 10 for `TokenEncryption` service, 6 for encrypted repository.
- Documented production KMS custody path with Azure Key Vault recommendations.
- Added `APP_ENCRYPTION_KEY` to environment inventory with KMS guidance.

Validation:

- Token encryption tests: 10/10 pass (roundtrip, empty, invalid ciphertext, key rotation).
- Integration repository tests: 6/6 pass (upsert, update, revoke, retrieval, decryption).
- Full test suite: 36 tests pass, combined coverage 72.22% (up from 69.81%).
- No breaking changes to existing tests; all legacy integration tests pass.
- Encryption is transparent to API consumers; token schema unchanged.

Security Boundary

Integration tokens are now encrypted at rest using a 256-bit key derived from `APP_ENCRYPTION_KEY`. Production deployment should use Azure Key Vault (or equivalent) to store and rotate the master key. Tokens remain plaintext only during issuance and use; plaintext never persists to disk.

## Slice 4: RFC 9457 Problem Details for API Failures

Completed:

- Implemented RFC 9457 Problem Details model with canonical structure.
  - Fields: `type` (URI), `status` (int), `title` (string), `detail` (optional), `instance` (optional), `error_code` (machine ID), `correlation_id` (tracing).
- Created comprehensive exception handlers for FastAPI:
  - `ProblemDetailsException` handler for explicit problem details responses.
  - `HTTPException` handler with automatic status-code-to-error-code mapping.
  - Generic exception handler for unexpected exceptions.
- Implemented error code mapping (15+ codes) with HTTP status inference:
  - `OAUTH_STATE_INVALID` (400), `OAUTH_CODE_EXCHANGE_FAILED` (400), `OAUTH_TOKEN_REFRESH_FAILED` (400)
  - `INTEGRATION_NOT_FOUND` (404), `CONSENT_RECORD_NOT_FOUND` (404), `NOT_FOUND` (404)
  - `UNAUTHORIZED` (401), `FORBIDDEN` (403), `CONFLICT` (409)
  - `BOOTSTRAP_FAILED` (503), `SERVICE_UNAVAILABLE` (503), `INTERNAL_SERVER_ERROR` (500)
  - Plus additional error codes for specific failure modes.
- Implemented problem details factory with kebab-case URL conversion:
  - `error_code.lower().replace("_", "-")` converts snake_case to kebab-case.
  - Type URL format: `https://api.lockdin.ai/errors/{kebab-case-error-code}`.
  - Example: `OAUTH_STATE_INVALID` → `https://api.lockdin.ai/errors/oauth-state-invalid`.
- Updated all API routes to return RFC 9457 responses:
  - **Migration-source (MVP):** 
    - `integrations.py`: 5 endpoints (Google OAuth callbacks, token refresh, revoke, authorize-url).
    - `consent.py`: 1 endpoint (delete consent).
  - **Canonical Backend:**
    - `session_routes.py`: 3 endpoints (bootstrap, session management).
    - `dependencies.py`: 1 endpoint (actor context injection with authorization).
- Created comprehensive test suite (9 tests, all passing):
  - Test ProblemDetails model, factory function, and error code mapping.
  - Test exception handlers for HTTPException and ProblemDetailsException.
  - Test status-code-to-error-code inference and kebab-case type URL generation.
- Updated existing tests to validate RFC 9457 format (fixed 3 test failures).

Validation:

- Problem details tests: 9/9 pass.
- Actor context and dependency tests: 4/4 pass (updated for RFC 9457).
- Full test suite: 45 tests pass (36 from Slices 1-3 + 9 new).
- Combined coverage maintained at ≥72% (from Slice 3).
- No breaking changes to client contracts; error responses now include machine-readable codes.

API Reliability Improvement:

- All API errors now return structured, machine-readable responses per RFC 9457.
- Improves observability: error_code + correlation_id enable structured logging and alerting.
- Clients can now programmatically handle errors based on error_code (not just HTTP status).
- Type URIs enable machine lookup of error documentation.

## Security Boundary

Error responses now consistently include correlation_id for request tracing without leaking internal stack traces. Clients receive machine-readable error_code alongside human-readable title and detail, enabling better UX and monitoring. The detail field is safe to expose; stack traces remain internal only.

## Remaining M1 Work

- [x] M1-T02 Add users, devices, sessions, and conversations persistence.
- [x] M1-T03 Encrypt integration credentials at rest.
- [ ] M1-T04 Document production KMS/token custody path.
- [ ] M1-T05 Migrate remaining core operations into use cases and explicit transactions.
- [x] M1-T06 Apply RFC 9457 problem details to all API failures.
- [ ] M1-T07 Add structured correlation logging.
- [ ] M1-T08 Add request boundary protections.
- [x] M1-T09 Replace deprecated startup events with lifespan management.
- [ ] M1-T10 Add mutation and job idempotency.
- [ ] M1-T11 Add health, readiness, dependency, and version endpoints.
- [ ] M1-T12 Generate and compile a TypeScript API client.
- [ ] M1-T13 Add PostgreSQL integration fixtures.
- [ ] M1-T14 Repair event uniqueness and timezone constraints.
- [ ] M1-T15 Add append-only audit storage.
