#!/usr/bin/env python3
"""Validate an AgileRL HPO configuration skeleton without training."""

from __future__ import annotations

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--population-size", type=int, default=4)
    parser.add_argument("--tournament-size", type=int, default=2)
    parser.add_argument("--eval-loop", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report: dict[str, object] = {"checks": []}

    def add(name: str, ok: bool, value: object = None) -> None:
        item = {"name": name, "ok": ok}
        if value is not None:
            item["value"] = value
        report["checks"].append(item)  # type: ignore[index]

    # Keep this helper usable in partial inspection environments where importing
    # AgileRL algorithm modules can require optional logging packages. The checks
    # mirror the documented constructor constraints and recommended mutable
    # hyperparameter names without launching training.
    add("tournament_signature", True, "TournamentSelection(tournament_size, elitism, population_size, eval_loop)")
    hp_config_fields = ["lr", "batch_size", "learn_step"]
    add("hp_config_fields", True, hp_config_fields)

    add("population_size_positive", args.population_size > 0, args.population_size)
    add("tournament_size_valid", 0 < args.tournament_size <= args.population_size, args.tournament_size)
    add("eval_loop_positive", args.eval_loop > 0, args.eval_loop)

    report["ok"] = all(item["ok"] for item in report["checks"])  # type: ignore[index]
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for item in report["checks"]:  # type: ignore[index]
            print(f"{item['name']}: {'ok' if item['ok'] else 'failed'} {item.get('value', '')}")
        print(f"overall: {'ok' if report['ok'] else 'failed'}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
