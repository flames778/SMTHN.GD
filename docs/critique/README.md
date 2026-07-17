# Milestone Critique Skills

This folder defines how every milestone implementation is critiqued and rated.

## What is included

- `milestone_pillars.json`: six custom SWE pillars per milestone, each with weights and checks.
- `scorecard_template.md`: human review template for implementation PRs.

## Scoring process

1. Pick a milestone id (`M0`..`M13`).
2. Score each of its six pillars from `0` to `5`.
3. Attach evidence for each score.
4. Run the scorer:

```powershell
python scripts/critique_milestone.py --milestone M0 --scores-json '{"Repository Hygiene":4,"Secret Safety":5,"Developer Experience":3,"Build Reproducibility":3,"Architecture Governance":4,"Migration Clarity":4}' --evidence-json '{"Secret Safety":"gitleaks passes in CI"}'
```

5. The command returns a weighted score out of 100 and pass/fail against the milestone threshold.

## Rule of use

- No milestone is considered complete without a saved scorecard.
- Any pillar scored below `3` must have an action item before merge.
- Any failed milestone score requires rework before the next milestone starts.
