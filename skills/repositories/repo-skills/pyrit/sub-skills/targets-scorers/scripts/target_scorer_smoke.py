#!/usr/bin/env python3
"""No-secret PyRIT target and scorer introspection smoke."""
from __future__ import annotations

import argparse
import importlib
import inspect
import json

OBJECTS = [
    ("pyrit.prompt_target", "TextTarget"),
    ("pyrit.prompt_target", "OpenAIChatTarget"),
    ("pyrit.prompt_target.http_target.http_target", "HTTPTarget"),
    ("pyrit.prompt_target.http_target.httpx_api_target", "HTTPXAPITarget"),
    ("pyrit.prompt_target.common.target_configuration", "TargetConfiguration"),
    ("pyrit.prompt_target.common.target_capabilities", "TargetCapabilities"),
    ("pyrit.score.true_false.substring_scorer", "SubStringScorer"),
    ("pyrit.score.true_false.self_ask_true_false_scorer", "SelfAskTrueFalseScorer"),
    ("pyrit.score.float_scale.self_ask_scale_scorer", "SelfAskScaleScorer"),
    ("pyrit.score.batch_scorer", "BatchScorer"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect target/scorer APIs without network, credentials, or prompt sends.")
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
    result = {"ok": not errors, "checks": checks, "errors": errors, "skipped": ["live OpenAI/Azure/HuggingFace/Playwright/HTTP sends require credentials or services"]}
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
