#!/usr/bin/env python3
"""Check Otter serving import prerequisites without starting services.

By default this checks installed packages only. Pass --repo-root to inspect a
specific Otter checkout for known serving-module import defects.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path


def check_module(module: str) -> dict:
    try:
        imported = importlib.import_module(module)
        return {"module": module, "status": "ok", "file": getattr(imported, "__file__", None)}
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report all import failures
        return {"module": module, "status": "error", "error_type": type(exc).__name__, "error": str(exc)}


def inspect_repo_root(repo_root: Path) -> list[dict]:
    results: list[dict] = []
    constants = repo_root / "pipeline" / "constants.py"
    serving_utils = repo_root / "pipeline" / "serve" / "serving_utils.py"
    results.append(
        {
            "check": "pipeline.constants file",
            "status": "ok" if constants.exists() else "missing",
            "path": "pipeline/constants.py",
            "advice": None
            if constants.exists()
            else "Serving modules import pipeline.constants before argparse. Add a compatibility module that re-exports CONTROLLER_HEART_BEAT_EXPIRATION, WORKER_HEART_BEAT_INTERVAL, and LOGDIR from pipeline.serve.serving_utils, or patch imports in the target checkout.",
        }
    )
    results.append(
        {
            "check": "serving_utils constants",
            "status": "ok" if serving_utils.exists() else "missing",
            "path": "pipeline/serve/serving_utils.py",
        }
    )
    model_worker = repo_root / "pipeline" / "serve" / "model_worker.py"
    if model_worker.exists():
        text = model_worker.read_text(errors="replace")
        has_flamingo_import = "from flamingo import FlamingoForConditionalGeneration" in text
        results.append(
            {
                "check": "model_worker flamingo import",
                "status": "warn" if has_flamingo_import else "ok",
                "path": "pipeline/serve/model_worker.py",
                "advice": "The worker imports a top-level flamingo module; installed otter-ai exposes FlamingoForConditionalGeneration through otter_ai. Patch this import before serving Flamingo checkpoints."
                if has_flamingo_import
                else None,
            }
        )
    else:
        results.append({"check": "model_worker file", "status": "missing", "path": "pipeline/serve/model_worker.py"})
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose Otter serving import prerequisites without launching services.")
    parser.add_argument("--repo-root", help="Optional target Otter checkout to inspect for serving compatibility files.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable output.")
    args = parser.parse_args()

    package_modules = ["otter_ai", "fastapi", "uvicorn", "gradio", "requests", "torch", "transformers"]
    results = [check_module(m) for m in package_modules]

    if args.repo_root:
        root = Path(args.repo_root).expanduser().resolve()
        results.append({"check": "repo_root", "status": "ok" if root.exists() else "missing", "path": str(root)})
        if root.exists():
            sys.path.insert(0, str(root))
            results.extend(inspect_repo_root(root))
            # Try these after sys.path insertion so the errors are explicit.
            for module in ["pipeline.serve.controller", "pipeline.serve.model_worker", "pipeline.serve.gradio_web_server"]:
                results.append(check_module(module))

    has_error = any(item.get("status") in {"error", "missing"} for item in results if item.get("module") or item.get("check") != "pipeline.constants file")
    has_warn_or_error = any(item.get("status") in {"error", "missing", "warn"} for item in results)

    if args.json:
        print(json.dumps({"schema": "otter.serving-import-check.v1", "results": results}, indent=2))
    else:
        for item in results:
            name = item.get("module") or item.get("check")
            status = item.get("status")
            print(f"{status.upper():7} {name}")
            if item.get("error"):
                print(f"        {item['error_type']}: {item['error']}")
            if item.get("advice"):
                print(f"        advice: {item['advice']}")
    return 2 if has_error else (1 if has_warn_or_error else 0)


if __name__ == "__main__":
    raise SystemExit(main())
