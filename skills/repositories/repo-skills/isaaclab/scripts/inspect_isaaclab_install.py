#!/usr/bin/env python3
"""Summarize the installed Isaac Lab packages and basic runtime readiness."""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from importlib import metadata

DEFAULT_DISTRIBUTIONS = [
    "isaaclab",
    "isaaclab_assets",
    "isaaclab_contrib",
    "isaaclab_experimental",
    "isaaclab_mimic",
    "isaaclab_newton",
    "isaaclab_ov",
    "isaaclab_ovphysx",
    "isaaclab_physx",
    "isaaclab_ppisp",
    "isaaclab_rl",
    "isaaclab_tasks",
    "isaaclab_tasks_experimental",
    "isaaclab_teleop",
    "isaaclab_visualizers",
]

DEFAULT_IMPORTS = [
    "isaaclab",
    "isaaclab.app.app_launcher",
    "isaaclab_assets",
    "isaaclab_tasks",
    "isaaclab_rl",
]


def _dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _probe_import(name: str) -> dict[str, object]:
    try:
        module = importlib.import_module(name)
        return {"ok": True, "version": getattr(module, "__version__", None)}
    except Exception as exc:  # pragma: no cover - small helper script
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _pip_check() -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "ok": result.returncode == 0,
        "exit_code": result.returncode,
        "output": (result.stdout or result.stderr).strip(),
    }


def _torch_summary() -> dict[str, object]:
    try:
        import torch

        summary: dict[str, object] = {
            "ok": True,
            "version": torch.__version__,
            "cuda": torch.version.cuda,
            "cuda_available": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count(),
        }
        if torch.cuda.is_available():
            summary["device_0_name"] = torch.cuda.get_device_name(0)
        return summary
    except Exception as exc:  # pragma: no cover - small helper script
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize the Isaac Lab installation.")
    parser.add_argument(
        "--distributions",
        nargs="*",
        default=DEFAULT_DISTRIBUTIONS,
        help="Distribution names to inspect.",
    )
    parser.add_argument(
        "--imports",
        nargs="*",
        default=DEFAULT_IMPORTS,
        help="Modules to import for a quick smoke check.",
    )
    args = parser.parse_args()

    report = {
        "python": {
            "version": sys.version.split()[0],
            "platform": sys.platform,
        },
        "pip_check": _pip_check(),
        "distributions": {name: _dist_version(name) for name in args.distributions},
        "imports": {name: _probe_import(name) for name in args.imports},
        "torch": _torch_summary(),
    }

    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["pip_check"]["ok"]:
        print("[WARN]: pip check reported issues; see the JSON output for details.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
