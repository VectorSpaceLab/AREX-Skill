from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_CHECKS = [
    "state_memory_preserved",
    "strategy_interruption_executed",
    "combat_priority_scored",
    "survival_rule_executed",
    "all_core_skills_invoked",
    "optimizer_step_executed",
]


def evaluate_proxy(trace: dict) -> dict:
    invocations = trace.get("invocations", [])
    invoked = {item.get("module") or item.get("skill") for item in invocations if isinstance(item, dict)}
    required_modules = set(trace.get("required_modules", []))
    checks = {
        "state_memory_preserved": bool(trace.get("state_memory", {}).get("levels")),
        "strategy_interruption_executed": bool(trace.get("strategy", {}).get("interrupted")),
        "combat_priority_scored": bool(trace.get("combat", {}).get("ranked_actions")),
        "survival_rule_executed": trace.get("survival", {}).get("action") not in {None, "none"},
        "all_core_skills_invoked": required_modules.issubset(invoked),
        "optimizer_step_executed": bool(trace.get("training_trace", {}).get("params_before") != trace.get("training_trace", {}).get("params_after")),
    }
    passed = sum(1 for name in REQUIRED_CHECKS if checks.get(name) is True)
    pass_rate = passed / len(REQUIRED_CHECKS)
    return {"mechanism_checks": checks, "mechanism_pass_rate": pass_rate, "passed_checks": passed, "required_checks": len(REQUIRED_CHECKS)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a soft-mode AutoAscend proxy recovery trace.")
    parser.add_argument("trace")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    trace = json.loads(Path(args.trace).read_text(encoding="utf-8"))
    result = evaluate_proxy(trace)
    Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
