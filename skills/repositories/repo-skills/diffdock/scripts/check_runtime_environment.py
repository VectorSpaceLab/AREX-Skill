#!/usr/bin/env python3
"""Check a DiffDock runtime context without launching expensive workflows.

Example:
  python scripts/check_runtime_environment.py --repo-root /path/to/diffdock-runtime --check-gnina
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
import shutil
import sys

MODULES = [
    "yaml",
    "numpy",
    "pandas",
    "torch",
    "torch_geometric",
    "rdkit",
    "prody",
    "esm",
    "openfold",
    "e3nn",
    "utils.parsing",
    "app.run_utils",
    "spyrmsd",
]


def import_status(name: str) -> dict:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - diagnostic tool
        return {"module": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"module": name, "ok": True, "version": getattr(module, "__version__", None)}


def torch_status() -> dict:
    try:
        import torch  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    info = {
        "ok": True,
        "version": getattr(torch, "__version__", None),
        "cuda_version": getattr(torch.version, "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
    }
    if torch.cuda.is_available():
        try:
            info["cuda_device_name"] = torch.cuda.get_device_name(0)
            info["cuda_capability"] = list(torch.cuda.get_device_capability(0))
            torch.empty((1,), device="cuda")
            info["cuda_allocation_ok"] = True
        except Exception as exc:  # noqa: BLE001
            info["cuda_allocation_ok"] = False
            info["cuda_error"] = f"{type(exc).__name__}: {exc}"
    return info


def main() -> int:
    parser = argparse.ArgumentParser(description="Check DiffDock runtime imports and optional backend tools.")
    parser.add_argument("--repo-root", help="DiffDock runtime checkout/project root to add to sys.path for script-style imports.")
    parser.add_argument("--config", default="default_inference_args.yaml", help="Config path to check relative to repo root when provided.")
    parser.add_argument("--model-dir", help="Optional score model directory to check for model_parameters.yml.")
    parser.add_argument("--confidence-model-dir", help="Optional confidence model directory to check for model_parameters.yml.")
    parser.add_argument("--check-gnina", action="store_true", help="Check whether the gnina executable is resolvable.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve() if args.repo_root else None
    if repo_root:
        sys.path.insert(0, str(repo_root))

    files = {}
    if repo_root:
        files["repo_root_exists"] = repo_root.exists()
        files["config_exists"] = (repo_root / args.config).exists()
    if args.model_dir:
        model_dir = Path(args.model_dir)
        files["model_parameters_exists"] = (model_dir / "model_parameters.yml").exists()
    if args.confidence_model_dir:
        confidence_dir = Path(args.confidence_model_dir)
        files["confidence_model_parameters_exists"] = (confidence_dir / "model_parameters.yml").exists()

    result = {
        "python": sys.version.split()[0],
        "cwd": "<current-working-directory>",
        "repo_root_added": bool(repo_root),
        "imports": [import_status(name) for name in MODULES],
        "torch": torch_status(),
        "files": files,
        "gnina": {"checked": args.check_gnina, "path": shutil.which("gnina") if args.check_gnina else None},
        "notes": [
            "This helper does not run inference, training, evaluation, downloads, ESM folding, GNINA, or a web server.",
            "Missing heavy imports are expected in planning-only environments; prepare the full runtime before expensive workflows.",
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
