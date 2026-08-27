#!/usr/bin/env python3
"""Check Deepchecks installation and optional workflow imports.

This helper is safe by default: it makes no network calls, uses no credentials,
and only imports packages or inspects distribution metadata. It sets
DISABLE_LATEST_VERSION_CHECK=True unless the caller already chose another value
so importing Deepchecks does not trigger the package's latest-version check.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from importlib import metadata
from typing import Dict, List


def _try_import(module: str) -> Dict[str, object]:
    try:
        imported = importlib.import_module(module)
    except Exception as exc:  # pragma: no cover - diagnostic branch
        return {
            "module": module,
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    return {
        "module": module,
        "ok": True,
        "version": getattr(imported, "__version__", None),
    }


def _dist_version(name: str) -> Dict[str, object]:
    try:
        return {"distribution": name, "ok": True, "version": metadata.version(name)}
    except metadata.PackageNotFoundError:
        return {"distribution": name, "ok": False, "error": "not installed"}


def build_report(args: argparse.Namespace) -> Dict[str, object]:
    os.environ.setdefault("DISABLE_LATEST_VERSION_CHECK", "True")

    modules: List[str] = ["deepchecks", "deepchecks.tabular"]
    if args.include_nlp:
        modules.extend(["deepchecks.nlp", "transformers", "sentence_transformers"])
    if args.include_nlp_properties:
        modules.extend(["fasttext"])
    if args.include_vision:
        modules.extend(["torch", "torchvision", "deepchecks.vision"])

    imports = [_try_import(module) for module in modules]
    distributions = [_dist_version("deepchecks")]

    if args.include_vision:
        torch_status = next((item for item in imports if item["module"] == "torch" and item["ok"]), None)
        if torch_status:
            try:
                import torch

                torch_status["cuda_available"] = bool(torch.cuda.is_available())
                torch_status["cuda_version"] = torch.version.cuda
                torch_status["device_count"] = int(torch.cuda.device_count()) if torch.cuda.is_available() else 0
            except Exception as exc:  # pragma: no cover
                torch_status["backend_probe_error"] = f"{type(exc).__name__}: {exc}"

    ok = all(item["ok"] for item in imports) and all(item["ok"] for item in distributions)
    return {
        "ok": ok,
        "python": sys.version.split()[0],
        "executable_basename": os.path.basename(sys.executable),
        "disable_latest_version_check": os.environ.get("DISABLE_LATEST_VERSION_CHECK"),
        "distributions": distributions,
        "imports": imports,
        "notes": [
            "Install deepchecks for tabular/base workflows.",
            "Install deepchecks[nlp] for NLP workflows and deepchecks[nlp-properties] for optional heavier text-property calculators.",
            "Install deepchecks[vision] plus a compatible torch/torchvision build for vision workflows; use a CUDA torch build only when GPU execution is required.",
        ],
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check Deepchecks base, NLP, and vision imports without running suites or downloading data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--include-nlp", action="store_true", help="Check Deepchecks NLP and core NLP dependencies.")
    parser.add_argument(
        "--include-nlp-properties",
        action="store_true",
        help="Also check optional fasttext-backed NLP property dependency.",
    )
    parser.add_argument("--include-vision", action="store_true", help="Check Deepchecks Vision plus torch/torchvision.")
    parser.add_argument("--fail-on-missing-optional", action="store_true", help="Return non-zero when a requested optional import fails.")
    args = parser.parse_args(argv)

    report = build_report(args)
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["ok"] and args.fail_on_missing_optional:
        return 1
    # Base deepchecks import failures are always actionable.
    base_import = next((item for item in report["imports"] if item["module"] == "deepchecks"), None)
    return 0 if base_import and base_import["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
