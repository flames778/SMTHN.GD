# ADR 0002: Persistence Boundary

- Status: Accepted (M0)
- Date: 2026-07-17

## Context

Current data concerns are mixed across API, service, and repository layers.

## Decision

Adopt PostgreSQL as canonical state store with SQLAlchemy repositories and explicit use-case layer transaction boundaries.

## Consequences

- Pros: stronger consistency and migration control.
- Cons: requires stricter schema governance and migration discipline.

## Follow-up

M1 adds actor/session entities, token encryption at rest, and auditable append-only events.
