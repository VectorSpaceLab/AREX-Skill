#!/usr/bin/env python3
"""Check a PyOD install and optional extras without mutating the environment.

This root-level helper is intentionally read-only: it imports PyOD, runs a tiny
IForest fit, probes selected optional modules with importlib, and optionally
prints JSON for automation.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys

OPTIONAL_MODULES = {
    "torch": "pyod[torch]",
    "torch_geometric": "pyod[graph]",
    "xgboost": "pyod[xgboost]",
    "suod": "pyod[suod]",
    "combo": "pyod[combo]",
    "pythresh": "pyod[pythresh]",
    "mcp": "pyod[mcp]",
    "sentence_transformers": "pyod[embedding]",
    "openai": "pyod[openai]",
    "transformers": "pyod[huggingface]",
    "librosa": "pyod[audio]",
    "soundfile": "pyod[audio]",
}


def run() -> dict[str, object]:
    import numpy as np
    import pyod
    from pyod.models.iforest import IForest

    X = np.random.RandomState(42).randn(40, 3)
    clf = IForest(n_estimators=10, contamination=0.1, random_state=42).fit(X)
    scores = clf.decision_function(X[:5])
    optional = {
        name: {
            "installed": importlib.util.find_spec(name) is not None,
            "extra": extra,
        }
        for name, extra in OPTIONAL_MODULES.items()
    }
    return {
        "status": "ok",
        "pyod_version": pyod.__version__,
        "iforest_score_shape": list(scores.shape),
        "iforest_train_labels": int(clf.labels_.sum()),
        "optional_modules": optional,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args(argv)
    try:
        result = run()
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "error", "error": str(exc)}, sort_keys=True))
        else:
            print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"PyOD version: {result['pyod_version']}")
        print(f"IForest score shape: {result['iforest_score_shape']}")
        missing = [k for k, v in result["optional_modules"].items() if not v["installed"]]
        print("Missing optional modules:", ", ".join(missing) if missing else "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
