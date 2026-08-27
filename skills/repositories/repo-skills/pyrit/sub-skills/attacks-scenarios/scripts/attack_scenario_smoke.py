#!/usr/bin/env python3
"""No-secret PyRIT attack/scenario introspection smoke."""
from __future__ import annotations

import argparse
import importlib
import inspect
import json

OBJECTS = [
    ("pyrit.executor.attack.single_turn.prompt_sending", "PromptSendingAttack"),
    ("pyrit.executor.attack.single_turn.skeleton_key", "SkeletonKeyAttack"),
    ("pyrit.executor.attack.multi_turn.crescendo", "CrescendoAttack"),
    ("pyrit.executor.attack.multi_turn.red_teaming", "RedTeamingAttack"),
    ("pyrit.executor.attack.compound.sequential_attack", "SequentialAttack"),
    ("pyrit.executor.attack.core.attack_config", "AttackConverterConfig"),
    ("pyrit.executor.attack.core.attack_config", "AttackScoringConfig"),
    ("pyrit.executor.attack.core.attack_config", "AttackAdversarialConfig"),
    ("pyrit.scenario", "Scenario"),
    ("pyrit.scenario.core.attack_technique_factory", "AttackTechniqueFactory"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect attack/scenario APIs without sending prompts or starting services.")
    parser.add_argument("--json", action="store_true", help="print JSON output")
    args = parser.parse_args()
    checks = []
    errors = []
    for module_name, attr in OBJECTS:
        try:
            obj = getattr(importlib.import_module(module_name), attr)
            checks.append({"object": f"{module_name}.{attr}", "signature": str(inspect.signature(obj))[:500]})
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{module_name}.{attr}: {type(exc).__name__}: {exc}")
    result = {"ok": not errors, "checks": checks, "errors": errors, "skipped": ["attack execution, model calls, dataset downloads, GCG/model downloads"]}
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
