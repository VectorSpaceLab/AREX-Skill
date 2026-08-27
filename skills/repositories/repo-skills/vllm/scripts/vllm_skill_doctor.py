#!/usr/bin/env python3
"""Safe vLLM environment doctor for agents.

This script checks import, distribution metadata, CLI availability, and backend
facts. It does not download models, start servers, or contact external APIs.
"""
from __future__ import annotations

import argparse
import importlib.metadata as metadata
import importlib.util
import json
import shutil
import subprocess
import sys
from typing import Any


def run(cmd: list[str], timeout: int) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "command": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:
        return {"command": cmd, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    parser.add_argument("--cli-help", action="store_true", help="Run `vllm --help`")
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args()

    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "executable_basename": sys.executable.rsplit("/", 1)[-1],
        "vllm_import": None,
        "vllm_distribution": None,
        "torch": None,
        "cli": {"path_found": shutil.which("vllm") is not None},
    }

    try:
        report["vllm_distribution"] = metadata.version("vllm")
    except metadata.PackageNotFoundError:
        report["vllm_distribution"] = "not installed"

    try:
        import vllm  # type: ignore

        report["vllm_import"] = {"ok": True, "version": getattr(vllm, "__version__", None)}
    except Exception as exc:
        report["vllm_import"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    if importlib.util.find_spec("torch") is not None:
        try:
            import torch  # type: ignore

            report["torch"] = {
                "version": getattr(torch, "__version__", None),
                "cuda_version": getattr(torch.version, "cuda", None),
                "cuda_available": bool(torch.cuda.is_available()),
                "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            }
        except Exception as exc:
            report["torch"] = {"error": f"{type(exc).__name__}: {exc}"}

    if args.cli_help:
        report["cli"]["help"] = run(["vllm", "--help"], args.timeout)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
        if report["vllm_import"] and not report["vllm_import"].get("ok"):
            print("\nImport failed: fix the active Python environment before running vLLM workflows.")
        elif report["torch"] and not report["torch"].get("cuda_available"):
            print("\nCUDA is not available in this Python. GPU serving still needs user-hardware verification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
