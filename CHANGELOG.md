# Changelog

All notable changes to this project are documented in this file.

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
