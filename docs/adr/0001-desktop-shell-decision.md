# ADR 0001: Desktop Shell Strategy

- Status: Proposed (M0)
- Date: 2026-07-17

## Context

Lockd'In needs an always-available Windows surface with tray presence, global shortcut support, and a secure local capability host.

## Decision

Prototype Tauri 2 first. Keep Electron as fallback if capability or stability blockers appear.

## Consequences

- Pros: lower resource usage, Rust-backed native boundary, good Windows packaging path.
- Cons: plugin and ecosystem maturity risks versus Electron.

## Validation Gate

Finalize in M3 using benchmark and reliability evidence.
