# Migration Source Boundaries

This repository currently contains migration-source code and future canonical runtime code.

## Migration sources (read and extract, do not expand)

- `jarvis.py`
- `lockdin_mvp/`
- `DeepSeek-V4-Pro/`
- `csm/`

## Canonical destinations for new implementation

- Backend domain and runtime: `apps/backend/` (to be created in M1).
- Web product and 3D experience: `apps/web/`.
- Windows shell: `apps/desktop/`.
- Shared TypeScript packages: `packages/`.
- Documentation and governance: `docs/`.

## Rule

New production features should target canonical destinations, not migration-source paths.
