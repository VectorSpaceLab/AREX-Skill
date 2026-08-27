#!/usr/bin/env python3
"""Probe the OptiMate package families from any working directory.

Safe by default: imports only, prints versions and optional CUDA visibility,
and never downloads data or launches training.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib import metadata
from pathlib import Path

MODULE_TO_DIST = {
    "speedster": "speedster",
    "nebullvm": "nebullvm",
    "forward_forward": "forward_forward",
    "open_alpha_tensor": "OpenAlphaTensor",
    "chatllama": "chatllama-py",
}


def add_repo_root(repo_root: str | None) -> None:
    if repo_root:
        sys.path.insert(0, str(Path(repo_root).resolve()))


def probe_module(name: str) -> dict:
    result = {"module": name, "status": "missing", "version": None, "file": None}
    try:
        module = importlib.import_module(name)
        result["status"] = "ok"
        result["file"] = getattr(module, "__file__", None)
    except Exception as exc:  # pragma: no cover - diagnostic helper
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result

    dist = MODULE_TO_DIST.get(name)
    if dist:
        try:
            result["version"] = metadata.version(dist)
        except Exception:
            result["version"] = None
    return result


def probe_cuda() -> dict:
    info = {"backend": "cuda", "status": "missing", "torch": None}
    try:
        import torch

        info["torch"] = torch.__version__
        info["status"] = "ok" if torch.cuda.is_available() else "unavailable"
        if torch.cuda.is_available():
            info["device_count"] = torch.cuda.device_count()
            info["device_name"] = torch.cuda.get_device_name(0)
            info["capability"] = list(torch.cuda.get_device_capability(0))
    except Exception as exc:  # pragma: no cover - diagnostic helper
        info["error"] = f"{type(exc).__name__}: {exc}"
    return info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modules", default="speedster,nebullvm", help="Comma-separated module names to import")
    parser.add_argument("--check-cuda", action="store_true", help="Also inspect torch CUDA visibility")
    parser.add_argument("--repo-root", default=None, help="Optional local checkout root to add to sys.path")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text")
    args = parser.parse_args()

    add_repo_root(args.repo_root)
    modules = [m.strip() for m in args.modules.split(",") if m.strip()]
    report = {
        "modules": [probe_module(m) for m in modules],
        "cuda": probe_cuda() if args.check_cuda else None,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for item in report["modules"]:
            line = f"{item['module']}: {item['status']}"
            if item.get("version"):
                line += f" {item['version']}"
            if item.get("file"):
                line += f" {item['file']}"
            print(line)
            if item.get("error"):
                print(f"  error: {item['error']}")
        if report["cuda"] is not None:
            print(json.dumps(report["cuda"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
