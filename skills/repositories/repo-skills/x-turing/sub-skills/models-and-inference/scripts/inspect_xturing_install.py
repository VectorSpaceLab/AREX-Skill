#!/usr/bin/env python3
"""Inspect the installed xTuring model and backend surface.

This is a read-only, model-focused diagnostic. It checks the package version,
model registry, selected model keys, and backend availability without downloading
weights or making network calls.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as md
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

REQUIRED_MODEL_KEYS = [
    "distilgpt2",
    "gpt2",
    "generic",
    "mistral_7b",
    "qwen3_0_6b",
    "gpt_oss_20b",
    "minimax_m2",
    "stable_diffusion",
]
OPTIONAL_MODULES = ["bitsandbytes", "deepspeed", "intel_extension_for_transformers"]


def _add_repo_root(repo_root: str | None) -> None:
    if not repo_root:
        return
    sys.path.insert(0, str(Path(repo_root).resolve()))


def _optional_status(module_name: str) -> Dict[str, Any]:
    try:
        importlib.import_module(module_name)
        return {"status": "ok"}
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"status": "missing-or-broken", "error": str(exc).splitlines()[0]}


def _selected_model_info(base_model, model_key: str) -> Dict[str, Any]:
    if model_key not in base_model.registry:
        raise KeyError(f"Unknown xTuring model key: {model_key}")

    model_cls = base_model.registry[model_key]
    return {
        "key": model_key,
        "class_name": model_cls.__name__,
        "config_name": getattr(model_cls, "config_name", None),
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect the installed xTuring model registry and backend readiness."
    )
    parser.add_argument(
        "--repo-root",
        help="Optional repository root to add to sys.path before importing xTuring.",
    )
    parser.add_argument(
        "--model-key",
        help="Optional model key to inspect inside the registry.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a human summary.",
    )
    args = parser.parse_args(argv)

    _add_repo_root(args.repo_root)

    try:
        import xturing
        from xturing.models import BaseModel
        import torch
        from xturing.utils.utils import is_itrex_available
    except Exception as exc:
        print(f"could not import xturing.models: {exc}", file=sys.stderr)
        return 1

    try:
        package_version = md.version("xturing")
    except Exception:  # pragma: no cover - metadata may be absent in editable envs
        package_version = None

    registry_keys = sorted(BaseModel.registry)
    missing_required = [key for key in REQUIRED_MODEL_KEYS if key not in BaseModel.registry]
    if missing_required:
        print(
            "missing required model registry keys: " + ", ".join(missing_required),
            file=sys.stderr,
        )
        return 1

    report: Dict[str, Any] = {
        "package_version": package_version,
        "module_file": str(Path(xturing.__file__).resolve()),
        "registry_size": len(registry_keys),
        "sample_keys": registry_keys[:12],
        "required_missing": missing_required,
        "torch": {
            "version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_device_count": torch.cuda.device_count(),
            "itrex_available": is_itrex_available(),
        },
        "optional": {name: _optional_status(name) for name in OPTIONAL_MODULES},
    }

    if args.model_key:
        try:
            report["selected_model"] = _selected_model_info(BaseModel, args.model_key)
        except Exception as exc:
            print(str(exc), file=sys.stderr)
            return 1

        key_lower = args.model_key.lower()
        quantized = any(token in key_lower for token in ("int8", "kbit"))
        if quantized and not report["torch"]["cuda_available"] and not report["torch"]["itrex_available"]:
            report.setdefault("warnings", []).append(
                "selected quantized model may require CUDA or the ITRex CPU path"
            )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    print(f"xTuring {report['package_version']} @ {report['module_file']}")
    print(f"registry size: {report['registry_size']}")
    print(f"sample keys: {', '.join(report['sample_keys'])}")
    print(f"torch: {report['torch']}")
    print(f"optional modules: {report['optional']}")
    if args.model_key:
        print(f"selected model: {report['selected_model']}")
        if report.get("warnings"):
            print(f"warnings: {report['warnings']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
