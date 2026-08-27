#!/usr/bin/env python3
"""Run no-download diagnostics for Stanza skill workflows.

The checker imports the base runtime, reports versions, and optionally inspects
CUDA, Java, and an existing Stanza resource directory. It never installs
packages, downloads models, starts CoreNLP, or mutates the resource cache.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

BASE_MODULES = {
    "stanza": "stanza",
    "torch": "torch",
    "numpy": "numpy",
    "requests": "requests",
    "protobuf": "google.protobuf",
    "networkx": "networkx",
    "tqdm": "tqdm",
    "huggingface-hub": "huggingface_hub",
    "platformdirs": "platformdirs",
    "emoji": "emoji",
    "udtools": "udtools",
}


def check_module(distribution: str, module_name: str) -> dict[str, Any]:
    """Import one module and return a JSON-serializable result."""
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # environment-specific diagnostic
        return {
            "ok": False,
            "distribution": distribution,
            "module": module_name,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    return {
        "ok": True,
        "distribution": distribution,
        "module": module_name,
        "version": getattr(module, "__version__", None),
        "path": getattr(module, "__file__", None),
    }


def check_java() -> dict[str, Any]:
    """Report Java availability without starting CoreNLP."""
    executable = shutil.which("java")
    if executable is None:
        return {"ok": False, "error": "java executable not found on PATH"}
    try:
        completed = subprocess.run(
            [executable, "-version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except Exception as exc:  # environment-specific diagnostic
        return {"ok": False, "path": executable, "error": str(exc)}
    output = (completed.stderr or completed.stdout).strip().splitlines()
    return {
        "ok": completed.returncode == 0,
        "path": executable,
        "returncode": completed.returncode,
        "version_line": output[0] if output else None,
    }


def check_resources(path: Path) -> dict[str, Any]:
    """Inspect an existing cache path without downloading or modifying it."""
    resolved = path.expanduser().resolve()
    manifest = resolved / "resources.json"
    languages: list[str] = []
    error: str | None = None
    if manifest.is_file():
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                languages = sorted(
                    key for key, value in payload.items()
                    if isinstance(key, str) and isinstance(value, dict)
                )
        except (OSError, json.JSONDecodeError) as exc:
            error = str(exc)
    result: dict[str, Any] = {
        "ok": resolved.is_dir() and manifest.is_file() and error is None,
        "path": str(resolved),
        "directory_exists": resolved.is_dir(),
        "manifest_exists": manifest.is_file(),
        "manifest": str(manifest),
        "manifest_language_entries": len(languages),
    }
    if error is not None:
        result["error"] = error
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Stanza's base runtime without downloads or server startup."
    )
    parser.add_argument(
        "--check-cuda",
        action="store_true",
        help="Report PyTorch CUDA build and device availability; CUDA is not required.",
    )
    parser.add_argument(
        "--check-java",
        action="store_true",
        help="Run 'java -version' only; no CoreNLP server is started.",
    )
    parser.add_argument(
        "--resources-dir",
        type=Path,
        default=None,
        help="Inspect an existing Stanza resource directory and resources.json.",
    )
    parser.add_argument(
        "--allow-missing-base",
        action="store_true",
        help="Report missing base imports but exit successfully (optional checks still report only).",
    )
    args = parser.parse_args()

    result: dict[str, Any] = {
        "ok": True,
        "side_effects": "none: no installs, downloads, cache writes, or server startup",
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
            "supported": sys.version_info >= (3, 9),
        },
        "environment": {
            "STANZA_RESOURCES_DIR": os.environ.get("STANZA_RESOURCES_DIR"),
            "STANZA_RESOURCES_URL": os.environ.get("STANZA_RESOURCES_URL"),
            "STANZA_RESOURCES_VERSION": os.environ.get("STANZA_RESOURCES_VERSION"),
            "STANZA_MODEL_URL": os.environ.get("STANZA_MODEL_URL"),
        },
        "modules": {},
    }

    if not result["python"]["supported"]:
        result["ok"] = False

    missing_base = False
    for distribution, module_name in BASE_MODULES.items():
        check = check_module(distribution, module_name)
        result["modules"][distribution] = check
        missing_base = missing_base or not check["ok"]
    if missing_base and not args.allow_missing_base:
        result["ok"] = False

    if args.check_cuda:
        torch_check = result["modules"]["torch"]
        if torch_check["ok"]:
            import torch

            available = bool(torch.cuda.is_available())
            result["cuda"] = {
                "checked": True,
                "available": available,
                "torch_cuda_version": torch.version.cuda,
                "device_count": torch.cuda.device_count() if available else 0,
            }
        else:
            result["cuda"] = {"checked": False, "available": False, "error": "torch import failed"}

    if args.check_java:
        result["java"] = check_java()

    if args.resources_dir is not None:
        result["resources"] = check_resources(args.resources_dir)

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
