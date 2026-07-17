# Model Routing Policy (M0 Baseline)

Purpose: choose the best model for each task category while preserving safety and reproducibility.

## Supported model labels

- `sol-5.6`: strongest for architecture synthesis, long-horizon planning, and policy design.
- `fable-5`: strongest for writing-heavy product docs, UX copy, and broad ideation.
- `kimi-2.7-code`: strongest for code generation, refactoring, and test authoring loops.

## Selection matrix

- Architecture, ADRs, system decomposition: `sol-5.6`
- Coding, migrations, tests, CI fixes: `kimi-2.7-code`
- Product narratives, onboarding docs, design concepts: `fable-5`
- Security policy and threat modeling: `sol-5.6`
- Mixed planning plus implementation: split by phase, plan with `sol-5.6`, implement with `kimi-2.7-code`

## Guardrails

- Use deterministic settings for infra/codegen tasks.
- Never switch models mid-task without recording why.
- Keep a short model-choice note in milestone scorecards.

## Current default for M0 execution

- Primary: `kimi-2.7-code` for file edits and automation scripts.
- Secondary: `sol-5.6` for milestone critiques and architectural gates.
