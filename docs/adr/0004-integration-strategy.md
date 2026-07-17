# ADR 0004: Integration Strategy

- Status: Accepted (M0)
- Date: 2026-07-17

## Context

Integration logic is currently bespoke and difficult to scale safely.

## Decision

Use a manifest-based connector registry with consent-gated capability exposure and typed sync events.

## Consequences

- Pros: reusable connector lifecycle, safer expansion to new providers.
- Cons: initial framework overhead.

## Follow-up

M5 introduces connector SDK contract, health model, cursor sync resilience, and post-Google connectors.
