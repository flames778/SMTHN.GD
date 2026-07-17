# CI Quality Thresholds (M0 Final)

These thresholds are enforced in `.github/workflows/ci.yml`.

## Required checks

- Lint formatting gate: `ruff format --check`
- Lint rule gate: `ruff check`
- Type gate: `mypy --strict` on automation scripts
- Test gate: `pytest` must pass
- Coverage gate: branch fails when app coverage is below `35%`
- Secret gate: `gitleaks` must pass on full git history

## Why 35% right now

M0 is a baseline-hardening milestone. The current test surface is still early-stage, so 35% is a minimum non-zero quality floor while M1-M3 expand coverage.

## Planned threshold ratchet

- M1 target: 45%
- M2 target: 55%
- M4 target: 65%
- M8+ target: 75%+
