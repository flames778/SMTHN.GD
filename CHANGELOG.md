# Changelog

All notable changes to this project are documented in this file.

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
