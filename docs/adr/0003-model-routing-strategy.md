# ADR 0003: Model Routing Strategy

- Status: Accepted (M0)
- Date: 2026-07-17

## Context

The product needs local-first privacy, fallback resilience, and provider flexibility.

## Decision

Implement provider adapter contract with policy-based router using latency, privacy tier, task class, and cost ceilings.

## Consequences

- Pros: vendor independence and deterministic degradation paths.
- Cons: added adapter maintenance overhead.

## Follow-up

M4 defines adapter contract, fallback behavior, routing telemetry, and streaming APIs.
