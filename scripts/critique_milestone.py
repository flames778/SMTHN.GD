from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
PILLARS_PATH = ROOT / "docs" / "critique" / "milestone_pillars.json"


def load_pillars() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(PILLARS_PATH.read_text(encoding="utf-8")))


def score_milestone(
    milestone: str,
    scores: dict[str, int],
    evidence: dict[str, str],
) -> dict[str, Any]:
    pillars_data = load_pillars()
    if milestone not in pillars_data["milestones"]:
        raise ValueError(f"unknown milestone: {milestone}")

    config = pillars_data["milestones"][milestone]
    total_weight = sum(item["weight"] for item in config["pillars"])
    weighted_score = 0.0
    pillar_results = []

    for pillar in config["pillars"]:
        name = pillar["name"]
        weight = pillar["weight"]
        value = scores.get(name)
        if value is None:
            raise ValueError(f"missing score for pillar '{name}'")
        if value < 0 or value > 5:
            raise ValueError(f"pillar '{name}' score must be between 0 and 5")

        weighted_score += value * weight
        pillar_results.append(
            {
                "name": name,
                "weight": weight,
                "score": value,
                "evidence": evidence.get(name, ""),
                "checks": pillar["checks"],
            }
        )

    normalized = round((weighted_score / total_weight) * 20, 2)
    status = "pass" if normalized >= config["pass_score"] else "fail"

    return {
        "milestone": milestone,
        "goal": config["goal"],
        "status": status,
        "score_100": normalized,
        "pass_score": config["pass_score"],
        "pillar_results": pillar_results,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Score a milestone implementation against custom SWE pillars."
    )
    parser.add_argument("--milestone", required=True, help="Milestone id, e.g. M0")
    parser.add_argument(
        "--scores-json",
        default=None,
        help="JSON object mapping pillar name to score 0..5",
    )
    parser.add_argument(
        "--scores-file",
        default=None,
        help="Path to JSON file mapping pillar name to score 0..5",
    )
    parser.add_argument(
        "--evidence-json",
        default="{}",
        help="JSON object mapping pillar name to evidence text",
    )
    parser.add_argument(
        "--evidence-file",
        default=None,
        help="Path to JSON file mapping pillar name to evidence text",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.scores_json and not args.scores_file:
        raise ValueError("provide either --scores-json or --scores-file")

    if args.scores_file:
        scores = json.loads(Path(args.scores_file).read_text(encoding="utf-8"))
    else:
        scores = json.loads(args.scores_json)

    if args.evidence_file:
        evidence = json.loads(Path(args.evidence_file).read_text(encoding="utf-8"))
    else:
        evidence = json.loads(args.evidence_json)

    result = score_milestone(args.milestone, scores, evidence)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
