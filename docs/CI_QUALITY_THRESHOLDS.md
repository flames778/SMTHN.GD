# CI Quality Thresholds (M0 Final)

These thresholds are enforced in `.github/workflows/ci.yml`.

## Required checks

- Lint formatting gate: `ruff format --check`
- Lint rule gate: `ruff check`
- Type gate: `mypy --strict` on automation scripts
- Test gate: `pytest` must pass
- Coverage gate: branch fails when app coverage is below `45%`
- Secret gate: `gitleaks` must pass on full git history

## Why 45% right now

M1 introduced the canonical backend package and identity boundary tests. The measured suite is above 60%, so 45% is the enforced floor while PostgreSQL integration coverage is added.

## Planned threshold ratchet

- M2 target: 55%
- M4 target: 65%
- M8+ target: 75%+
