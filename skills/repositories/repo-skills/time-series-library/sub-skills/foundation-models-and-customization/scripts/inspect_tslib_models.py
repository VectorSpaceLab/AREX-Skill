#!/usr/bin/env python3
"""Inspect TSLib model modules without training or downloading data.

Run this bundled helper with --repo-root pointing at a Time-Series-Library
checkout. It imports requested model modules and reports whether they expose a
TSLib-compatible `Model` or same-name class. Optional dependency failures are
reported without hiding core model failures.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

DEFAULT_MODELS = ["DLinear", "TimesNet", "TimeXer", "PatchTST", "Transformer"]
OPTIONAL_MODELS = ["Mamba", "MambaSingleLayer", "Chronos", "Chronos2", "TimesFM", "Moirai", "TiRex", "Sundial", "TimeMoE"]


def inspect_model(name: str, optional: bool = False) -> dict:
    module_name = f"models.{name}"
    out = {"model": name, "module": module_name, "import_ok": False, "class_ok": False, "optional": optional}
    try:
        module = importlib.import_module(module_name)
        out["import_ok"] = True
        out["file"] = str(getattr(module, "__file__", ""))
        if hasattr(module, "Model"):
            out["class_ok"] = True
            out["class_name"] = "Model"
        elif hasattr(module, name):
            out["class_ok"] = True
            out["class_name"] = name
        else:
            out["error"] = f"module has no class 'Model' or '{name}'"
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect TSLib model imports and class contracts without training.")
    parser.add_argument("--repo-root", default=".", help="Path to a Time-Series-Library checkout containing models/.")
    parser.add_argument("--models", nargs="*", default=DEFAULT_MODELS, help="Model basenames to inspect.")
    parser.add_argument("--optional-models", action="store_true", help="Also inspect known optional Mamba/LTSM model files.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    if not (root / "models").is_dir():
        print(f"FAIL: models/ not found under {root}")
        return 2

    sys.path.insert(0, str(root))
    names = list(args.models)
    if args.optional_models:
        for name in OPTIONAL_MODELS:
            if name not in names:
                names.append(name)

    required = set(args.models)
    results = [inspect_model(name, optional=name not in required) for name in names]
    if args.json:
        print(json.dumps({"repo_root": str(root), "models": results}, indent=2))
    else:
        for item in results:
            if item["import_ok"] and item["class_ok"]:
                status = "OK"
            elif item.get("optional"):
                status = "OPTIONAL-BLOCK"
            else:
                status = "BLOCK"
            print(status, item["model"], item.get("class_name", ""), item.get("error", ""))

    failed_required = [r for r in results if r["model"] in required and not (r["import_ok"] and r["class_ok"])]
    return 1 if failed_required else 0


if __name__ == "__main__":
    raise SystemExit(main())
