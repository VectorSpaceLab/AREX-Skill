#!/usr/bin/env python3
"""Safe AReaL environment doctor.

This script checks importability, package metadata, CLI availability, and optional
backend visibility. It never launches training, starts services, downloads models,
or uses credentials.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def _import(name: str) -> Check:
    try:
        mod = importlib.import_module(name)
        loc = getattr(mod, "__file__", "built-in-or-namespace")
        return Check(f"import:{name}", True, str(loc))
    except Exception as exc:  # pragma: no cover - diagnostic path
        return Check(f"import:{name}", False, f"{type(exc).__name__}: {exc}")


def _dist(name: str) -> Check:
    try:
        return Check(f"dist:{name}", True, metadata.version(name))
    except Exception as exc:  # pragma: no cover
        return Check(f"dist:{name}", False, f"{type(exc).__name__}: {exc}")


def _cli(command: list[str], timeout: float) -> Check:
    exe = shutil.which(command[0])
    if exe is None:
        return Check("cli:" + " ".join(command), False, f"{command[0]!r} not on PATH")
    try:
        proc = subprocess.run(
            [exe, *command[1:], "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        out = (proc.stdout or proc.stderr).splitlines()[:4]
        return Check("cli:" + " ".join(command), proc.returncode == 0, " | ".join(out))
    except Exception as exc:  # pragma: no cover
        return Check("cli:" + " ".join(command), False, f"{type(exc).__name__}: {exc}")


def _torch_cuda() -> Check:
    try:
        import torch

        detail: dict[str, Any] = {
            "torch": getattr(torch, "__version__", "unknown"),
            "cuda_version": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
        if torch.cuda.is_available():
            detail["device0"] = torch.cuda.get_device_name(0)
            detail["capability0"] = torch.cuda.get_device_capability(0)
            torch.empty((1,), device="cuda")
        return Check("backend:torch-cuda", True, json.dumps(detail, default=str))
    except Exception as exc:  # pragma: no cover
        return Check("backend:torch-cuda", False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument("--timeout", type=float, default=10.0, help="CLI help timeout in seconds.")
    parser.add_argument("--extra-import", action="append", default=[], help="Additional import name to check.")
    args = parser.parse_args()

    modules = [
        "areal",
        "areal.api.cli_args",
        "areal.dataset",
        "areal.reward.gsm8k",
        "areal.workflow.rlvr",
        "areal.v2.cli.cli",
        *args.extra_import,
    ]
    checks = [_dist("areal"), *[_import(m) for m in modules]]
    checks += [_cli(["areal"], args.timeout), _cli(["areal", "inf"], args.timeout), _cli(["areal", "agent"], args.timeout), _cli(["areal", "train"], args.timeout)]
    checks.append(_torch_cuda())

    if args.json:
        print(json.dumps({"python": sys.version, "checks": [asdict(c) for c in checks]}, indent=2))
    else:
        print(f"Python: {sys.version.split()[0]}")
        for c in checks:
            status = "OK" if c.ok else "FAIL"
            print(f"[{status}] {c.name}: {c.detail}")
        print("\nThis doctor does not prove full SGLang/vLLM/Megatron/FSDP/Archon/Ray/Slurm runtime behavior.")
    return 0 if all(c.ok for c in checks if not c.name.startswith("backend:torch-cuda")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
