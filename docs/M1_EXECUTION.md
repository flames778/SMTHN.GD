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

## Security Boundary

`X-Lockdin-User-Id` currently proves identity propagation, not authentication. A trusted local host or authenticated session layer must issue actor context before external exposure. Routes no longer invent identity, but header spoofing remains blocked only by the future authenticated boundary.

## Remaining M1 Work

- [ ] M1-T02 Add users, devices, sessions, and conversations persistence.
- [ ] M1-T03 Encrypt integration credentials at rest.
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
