# Changelog

All notable changes to this project are documented in this file.

## Unreleased - M1 Structured Correlation Logging

### Added
- `CorrelationIdMiddleware` for generating and extracting correlation IDs.
  - Auto-generates UUID4 if not provided in X-Correlation-ID header.
  - Enables external trace ID propagation for distributed tracing.
  - Injects correlation_id into all response headers.
- `StructuredLogger` for JSON-formatted structured logging.
  - Emits logs with timestamp, level, message, correlation_id, and actor context.
  - Supports multiple log levels: info, error, warning, debug.
  - Includes additional structured fields via **kwargs.
- Context variables for request-scoped data.
  - `_correlation_id`: Unique request identifier.
  - `_user_id` and `_device_id`: Actor identity for structured logs.
  - Helper functions: `get_correlation_id()`, `set_actor_context()`, `get_actor_context()`.
- Automatic correlation_id injection in error responses.
  - Exception handlers automatically capture and inject correlation_id.
  - All RFC 9457 Problem Details now include correlation_id.
  - Error tracing and debugging enabled without exposing stack traces.
- Comprehensive test suite (13 tests, all passing).
  - Middleware: ID generation, extraction, header propagation (4 tests).
  - Structured logging: JSON format, log levels, timestamps (3 tests).
  - Actor context: storage, retrieval, logging integration (3 tests).
  - Integration: endpoint tracing, error tracing, ID regeneration (3 tests).

### Changed
- Exception handlers updated to inject correlation_id into responses.
- `ProblemDetailsException` handler captures correlation_id before response.
- `HTTPException` handler injects correlation_id into problem details.
- Generic exception handler adds correlation_id to error responses.
- MVP app registers CorrelationIdMiddleware during startup.

### Observability
- Full end-to-end request tracing via correlation IDs.
- Structured JSON logs for centralized log aggregation.
- Actor identity (user_id, device_id) in all logs.
- Error responses include correlation_id for support and debugging.
- Integration with log aggregation platforms (ELK, Datadog, etc.).

## Unreleased - M1 RFC 9457 Problem Details

### Added
- RFC 9457 Problem Details model for standardized HTTP error responses.
- Comprehensive FastAPI exception handlers:
  - `ProblemDetailsException` handler for explicit problem details.
  - `HTTPException` handler with automatic status-to-error-code mapping.
  - Generic exception handler for unexpected errors.
- Error code mapping (15+) with HTTP status code inference:
  - OAuth errors: OAUTH_STATE_INVALID, OAUTH_CODE_EXCHANGE_FAILED, OAUTH_TOKEN_REFRESH_FAILED.
  - Integration errors: INTEGRATION_NOT_FOUND, UNSUPPORTED_INTEGRATION, REFRESH_TOKEN_NOT_AVAILABLE.
  - Authorization: UNAUTHORIZED, FORBIDDEN, INVALID_SETUP_SECRET.
  - Server: BOOTSTRAP_FAILED, INTERNAL_SERVER_ERROR, SERVICE_UNAVAILABLE.
- Problem details factory with kebab-case type URL conversion.
- Correlation ID support for request tracing (optional).
- Comprehensive test suite (9 tests, all passing).

### Changed
- All API error responses now return RFC 9457 Problem Details format.
- Error type URIs: `https://api.lockdin.ai/errors/{kebab-case-error-code}`.
- HTTP status inference from error codes (e.g., UNAUTHORIZED → 401).
- Migration-source (MVP) routes: integrations (5), consent (1).
- Canonical backend routes: session routes (3), actor dependency (1).
- Exception handlers registered in main.py and test apps.

### Security
- Error responses include correlation_id for structured tracing without exposing stack traces.
- Machine-readable error_code enables client-side error handling and logging.
- detail field is safe to expose; internal traces remain server-side only.

## Unreleased - M1 Token Encryption

### Added
- `TokenEncryption` service with Fernet (AES-128-CBC + HMAC-SHA256) symmetric encryption.
- Automatic encryption of OAuth tokens on storage via `IntegrationRepository`.
- Transparent decryption via `get_decrypted_tokens()` for token consumption.
- Comprehensive test suite: 10 tests for encryption service, 6 for encrypted repository.
- Production KMS custody documentation with Azure Key Vault recommendations.
- `APP_ENCRYPTION_KEY` environment variable to environment inventory.

### Changed
- `IntegrationRepository.upsert_google()` now encrypts tokens before persistence.
- `IntegrationRepository.update_tokens()` encrypts new token values.
- `/api/integrations/{provider}/refresh` endpoint decrypts refresh token before OAuth exchange.
- `sync_google_integrations()` worker decrypts access token before integration sync.
- Configuration validation now enforces non-empty `APP_ENCRYPTION_KEY`.

### Security
- OAuth tokens (access_token, refresh_token) no longer stored in plaintext.
- Encryption transparent to API consumers; token schema unchanged.
- Database breach no longer exposes valid OAuth tokens without `APP_ENCRYPTION_KEY`.

## 2026-07-17 - M1 Identity Persistence

### Added
- Persistent users, devices, sessions, and conversations schema.
- One-time owner bootstrap endpoint protected by a separate setup secret.
- Opaque session tokens stored only as SHA-256 digests.
- Session expiry, revocation, active-user, and ownership enforcement.
- Alembic migration `0003_identity_and_conversations`.

### Changed
- Protected APIs now derive `ActorContext` from `X-Lockdin-Session-Token` instead of caller-supplied identity headers.
- Initial-owner bootstrap is concurrency-safe through a database uniqueness constraint.

## 2026-07-17 - M1 Identity Foundation

### Added
- Canonical backend package under `apps/backend/lockdin_backend`.
- Immutable `ActorContext` carrying user, device, and session identity.
- FastAPI actor dependency with problem-details-style unauthorized responses.
- Consent application use case with explicit repository and unit-of-work ports.
- Route and use-case tests for identity enforcement and consent ownership.
- Model asset assessment for DeepSeek V4 Pro and Sesame CSM.
- M1 execution log and six-pillar milestone critique evidence.

### Changed
- Protected consent and integration routes now require actor context instead of inventing a local user.
- Google sync jobs now receive user identity explicitly across the Celery boundary.
- FastAPI startup configuration now uses lifespan management.
- CI now checks canonical backend formatting, linting, strict typing, tests, and a 45% coverage floor.
- Developer diagnostics distinguish model source code from runnable checkpoints and voice assets.
- Vendor model submodules no longer block product repository status checks.

### Removed
- Hardcoded `MVP_USER_ID` and `local-user` identity from product application code.
- Tracked Python bytecode artifacts.

### Commits
- 1ea873f - feat(m1): propagate actor context across APIs and jobs
- 83e0f48 - ci(m1): enforce canonical backend quality gates
- 0b6c8c7 - chore(models): clarify optional provider asset readiness
- f912d80 - docs(m1): record identity slice evidence and critique
- 802ad10 - chore(repo): stop tracking generated Python bytecode

## 2026-07-17 - M0 Finalization

### Added
- Root repository baseline and developer tooling:
  - Added root ignore and pre-commit configuration for hygiene and secret protection.
  - Added Python project metadata and lockfile baselines.
  - Added workspace package manifest and developer automation scripts.
- Milestone critique framework:
  - Added six-pillar milestone scoring model and scoring utility.
  - Added critique templates, sample inputs, and M0 scorecard artifacts.
- Governance and architecture documentation:
  - Added master roadmap, M0 execution log, environment inventory, migration boundaries, and model routing policy.
  - Added ADR set for desktop shell, persistence boundary, model routing, and integration strategy.

### Changed
- CI quality pipeline now enforces explicit gates:
  - Lint formatting and lint rule checks.
  - Strict type checking for automation scripts.
  - Unit tests with minimum coverage threshold.
  - Full-history secret scanning.
- Root environment example now reflects Lockd'In runtime inventory and ownership model.
- Historical plan handoff now points to the canonical roadmap.

### Commits
- 215e0d0 - chore(m0): establish repository baseline and developer tooling
- f4def99 - ci(m0): enforce quality and secret scanning thresholds
- 85b45ac - docs(m0): finalize governance, critique framework, and closure artifacts
