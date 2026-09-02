#!/usr/bin/env python3
"""Evaluation metrics for RLAIF recovery artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def normalize_label(value) -> int:
    if value in {0, "0"}:
        return 1
    label = int(value)
    if label not in {1, 2}:
        raise ValueError(f"label must identify candidate 1 or 2, got {value!r}")
    return label


def preference_argmax(preference: list[float]) -> int | None:
    if len(preference) != 2:
        raise ValueError("preference must have length 2")
    if abs(float(preference[0]) - float(preference[1])) < 1e-12:
        return None
    return 1 if float(preference[0]) > float(preference[1]) else 2


def alignment_accuracy(records: list[dict]) -> dict:
    correct = 0
    total = 0
    ties = 0
    for item in records:
        pred = preference_argmax(item["preference"])
        if pred is None:
            ties += 1
            continue
        gold = normalize_label(item["human_label"])
        total += 1
        correct += int(pred == gold)
    return {
        "alignment_accuracy": correct / total if total else 0.0,
        "alignment_count": total,
        "alignment_correct": correct,
        "alignment_ties": ties,
    }


def win_rate(records: list[dict], policy: str) -> dict:
    wins = sum(1 for item in records if item.get("winner") == policy)
    total = len(records)
    return {"win_rate": wins / total if total else 0.0, "win_count": wins, "win_total": total}


def harmless_rate(records: list[dict]) -> dict:
    harmless = sum(1 for item in records if bool(item.get("harmless")))
    total = len(records)
    return {"harmless_rate": harmless / total if total else 0.0, "harmless_count": harmless, "harmless_total": total}


def target_consistency(plan_target: dict, recovery_target: dict) -> dict:
    issues = []
    for key in ["dataset", "metric"]:
        if str(plan_target.get(key, "")).strip().lower() != str(recovery_target.get(key, "")).strip().lower():
            issues.append(f"{key} mismatch")
    plan_value = float(plan_target.get("paper_value", plan_target.get("value", 0.0)))
    recovery_value = float(recovery_target.get("paper_value", recovery_target.get("value", 0.0)))
    if abs(plan_value - recovery_value) > 1e-9:
        issues.append("paper_value mismatch")
    return {"target_consistency_ok": not issues, "target_issues": issues}


def compute_metrics(data: dict) -> dict:
    result = {}
    if data.get("alignment_records") is not None:
        result.update(alignment_accuracy(data["alignment_records"]))
    if data.get("win_records") is not None:
        result.update(win_rate(data["win_records"], data.get("policy", "RLAIF")))
    if data.get("harmless_records") is not None:
        result.update(harmless_rate(data["harmless_records"]))
    if data.get("plan_target") and data.get("recovery_target"):
        result.update(target_consistency(data["plan_target"], data["recovery_target"]))
    return result


def smoke_data() -> dict:
    return {
        "alignment_records": [
            {"preference": [0.8, 0.2], "human_label": 1},
            {"preference": [0.4, 0.6], "human_label": 2},
            {"preference": [0.5, 0.5], "human_label": 1},
        ],
        "win_records": [{"winner": "RLAIF"}, {"winner": "SFT"}, {"winner": "RLAIF"}],
        "policy": "RLAIF",
        "harmless_records": [{"harmless": True}, {"harmless": False}, {"harmless": True}],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    data = smoke_data() if args.smoke or not args.input else json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = compute_metrics(data)
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
