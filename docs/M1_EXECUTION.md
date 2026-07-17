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

## Remaining M1 Work

- [x] M1-T02 Add users, devices, sessions, and conversations persistence.
- [x] M1-T03 Encrypt integration credentials at rest.
- [ ] M1-T04 Document production KMS/token custody path.
- [ ] M1-T05 Migrate remaining core operations into use cases and explicit transactions.
- [ ] M1-T06 Apply RFC 9457 problem details to all API failures.
- [ ] M1-T07 Add structured correlation logging.
- [ ] M1-T08 Add request boundary protections.
- [x] M1-T09 Replace deprecated startup events with lifespan management.
- [ ] M1-T10 Add mutation and job idempotency.
- [ ] M1-T11 Add health, readiness, dependency, and version endpoints.
- [ ] M1-T12 Generate and compile a TypeScript API client.
- [ ] M1-T13 Add PostgreSQL integration fixtures.
- [ ] M1-T14 Repair event uniqueness and timezone constraints.
- [ ] M1-T15 Add append-only audit storage.
