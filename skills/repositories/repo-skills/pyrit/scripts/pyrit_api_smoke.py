#!/usr/bin/env python3
"""No-secret PyRIT import and API smoke helper.

Run from any directory with an environment where `pyrit` is installed:
    python pyrit_api_smoke.py --json
The script performs imports/introspection only; it does not contact model APIs,
start servers, download datasets, or write persistent memory.
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from importlib import metadata

CHECKS = [
    ("pyrit", None),
    ("pyrit.converter", "Base64Converter"),
    ("pyrit.prompt_target", "TextTarget"),
    ("pyrit.score.true_false.substring_scorer", "SubStringScorer"),
    ("pyrit.memory", "CentralMemory"),
    ("pyrit.setup", "initialize_pyrit_async"),
    ("pyrit.executor.attack.single_turn.prompt_sending", "PromptSendingAttack"),
]


def describe(module_name: str, attr: str | None) -> dict[str, str]:
    module = importlib.import_module(module_name)
    if attr is None:
        return {"module": module_name, "status": "ok"}
    obj = getattr(module, attr)
    try:
        sig = str(inspect.signature(obj))
    except (TypeError, ValueError):
        sig = "<signature unavailable>"
    return {"module": module_name, "attribute": attr, "status": "ok", "signature": sig[:500]}


def main() -> int:
    parser = argparse.ArgumentParser(description="Import and introspect core PyRIT APIs without secrets or network.")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()
    result: dict[str, object] = {"ok": True, "checks": [], "warnings": []}
    try:
        result["distribution_version"] = metadata.version("pyrit")
    except metadata.PackageNotFoundError:
        result["ok"] = False
        result.setdefault("errors", []).append("distribution metadata for 'pyrit' was not found")
    for module_name, attr in CHECKS:
        try:
            result["checks"].append(describe(module_name, attr))  # type: ignore[index]
        except Exception as exc:  # noqa: BLE001 - diagnostic helper should report all import failures
            result["ok"] = False
            result.setdefault("errors", []).append(f"{module_name}:{attr or ''}: {type(exc).__name__}: {exc}")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("PyRIT API smoke:", "ok" if result["ok"] else "failed")
        if "distribution_version" in result:
            print("distribution_version:", result["distribution_version"])
        for check in result["checks"]:  # type: ignore[index]
            print("-", check)
        for err in result.get("errors", []):  # type: ignore[union-attr]
            print("ERROR:", err, file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
