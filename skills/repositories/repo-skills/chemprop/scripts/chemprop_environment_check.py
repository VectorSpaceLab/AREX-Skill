#!/usr/bin/env python3
"""Print safe Chemprop environment diagnostics for agents.

This helper avoids local path disclosure by reporting package versions,
importability, CLI availability, registry values, and PyTorch backend basics.
"""

from __future__ import annotations

import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys


def dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def import_ok(name: str) -> tuple[bool, str | None]:
    try:
        importlib.import_module(name)
        return True, None
    except Exception as exc:  # pragma: no cover - diagnostic helper
        return False, f"{type(exc).__name__}: {exc}"


def command_help(command: list[str]) -> dict[str, object]:
    executable = shutil.which(command[0])
    if executable is None:
        return {"command": " ".join(command), "available": False, "returncode": None}
    try:
        proc = subprocess.run(command + ["--help"], text=True, capture_output=True, timeout=20)
        return {
            "command": " ".join(command + ["--help"]),
            "available": True,
            "returncode": proc.returncode,
            "first_line": (proc.stdout or proc.stderr).splitlines()[0] if (proc.stdout or proc.stderr) else "",
        }
    except Exception as exc:  # pragma: no cover - diagnostic helper
        return {"command": " ".join(command + ["--help"]), "available": True, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    report: dict[str, object] = {
        "python_version": sys.version.split()[0],
        "distributions": {name: dist_version(name) for name in ["chemprop", "torch", "lightning", "rdkit", "numpy", "pandas", "scikit-learn", "scipy"]},
        "imports": {},
        "cli_help": [],
    }

    for module in ["chemprop", "chemprop.cli.main", "chemprop.data", "chemprop.featurizers", "chemprop.models", "chemprop.nn", "chemprop.uncertainty"]:
        ok, error = import_ok(module)
        report["imports"][module] = {"ok": ok, "error": error}

    for command in [["chemprop"], ["chemprop", "train"], ["chemprop", "predict"], ["chemprop", "fingerprint"], ["chemprop", "convert"], ["chemprop", "hpopt"]]:
        report["cli_help"].append(command_help(command))

    try:
        import torch

        report["torch_backend"] = {
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
    except Exception as exc:  # pragma: no cover - diagnostic helper
        report["torch_backend"] = {"error": f"{type(exc).__name__}: {exc}"}

    print(json.dumps(report, indent=2, sort_keys=True))
    failed_imports = [name for name, value in report["imports"].items() if not value["ok"]]
    return 1 if failed_imports else 0


if __name__ == "__main__":
    raise SystemExit(main())
