#!/usr/bin/env python3
"""Safe FedML install/import/CLI smoke check.

This helper is intentionally offline: it imports the package and renders help/version
output, but it does not login, launch, upload, deploy, or query remote resources.
"""

from __future__ import annotations

import argparse
import importlib
import shutil
import subprocess
import sys
from typing import Iterable


def run_command(cmd: Iterable[str], timeout: int) -> tuple[int, str, str]:
    proc = subprocess.run(
        list(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def main() -> int:
    parser = argparse.ArgumentParser(description="Check FedML import and offline CLI help/version.")
    parser.add_argument("--skip-cli", action="store_true", help="Only check Python imports.")
    parser.add_argument("--cuda", action="store_true", help="Also print torch CUDA availability.")
    parser.add_argument("--timeout", type=int, default=25, help="Timeout in seconds per CLI command.")
    args = parser.parse_args()

    try:
        fedml = importlib.import_module("fedml")
    except Exception as exc:  # pragma: no cover - troubleshooting path
        print(f"[FAIL] import fedml: {exc!r}", file=sys.stderr)
        return 1

    print(f"[OK] fedml import: version={getattr(fedml, '__version__', '<unknown>')}")
    print(f"[OK] fedml path: {getattr(fedml, '__file__', '<unknown>')}")

    required_attrs = ["init", "load_arguments", "run_simulation", "api"]
    missing = [name for name in required_attrs if not hasattr(fedml, name)]
    if missing:
        print(f"[FAIL] missing top-level attributes: {missing}", file=sys.stderr)
        return 2
    print(f"[OK] top-level attrs: {', '.join(required_attrs)}")

    # Import representative submodules/classes without starting servers or backend calls.
    # `fedml.serving` and `fedml.workflow` are importable subpackages but are not
    # eagerly attached as top-level attributes on `import fedml` in this release.
    checks = [
        ("fedml.api", "launch_job"),
        ("fedml.api", "run_list"),
        ("fedml.serving", "FedMLPredictor"),
        ("fedml.serving", "FedMLInferenceRunner"),
        ("fedml.workflow", "Workflow"),
        ("fedml.workflow", "Job"),
    ]
    for module_name, attr in checks:
        module = importlib.import_module(module_name)
        if not hasattr(module, attr):
            print(f"[FAIL] {module_name}.{attr} missing", file=sys.stderr)
            return 3
    print("[OK] representative API imports")

    if args.cuda:
        try:
            import torch
            print(f"[INFO] torch={torch.__version__} cuda={getattr(torch.version, 'cuda', None)}")
            print(f"[INFO] torch.cuda.is_available={torch.cuda.is_available()}")
            print(f"[INFO] torch.cuda.device_count={torch.cuda.device_count()}")
        except Exception as exc:  # pragma: no cover - optional path
            print(f"[WARN] CUDA check failed: {exc!r}")

    if not args.skip_cli:
        fedml_bin = shutil.which("fedml")
        if not fedml_bin:
            print("[FAIL] fedml executable not found on PATH", file=sys.stderr)
            return 4
        print(f"[OK] fedml executable: {fedml_bin}")

        for cmd in ([fedml_bin, "--help"], [fedml_bin, "version"]):
            code, stdout, stderr = run_command(cmd, timeout=args.timeout)
            command_text = " ".join(cmd)
            if code != 0:
                print(f"[FAIL] {command_text} exited {code}", file=sys.stderr)
                if stdout:
                    print(stdout[-1200:], file=sys.stderr)
                if stderr:
                    print(stderr[-1200:], file=sys.stderr)
                return 5
            preview = stdout.strip().splitlines()[:3]
            print(f"[OK] {command_text}: {' | '.join(preview)}")

    print("[PASS] FedML offline install smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
