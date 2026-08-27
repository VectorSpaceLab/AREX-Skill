#!/usr/bin/env python3
"""Safe XTuner installed-package and backend probe.

This helper imports only installed packages and runs optional CLI --help checks.
It does not download models, start training, start Ray, or require an XTuner
source checkout.

Examples:
  python scripts/check_xtuner_install.py --json
  python scripts/check_xtuner_install.py --check-sft-help --check-rl-help
"""
from __future__ import annotations

import argparse
import contextlib
import importlib
import importlib.metadata as md
import io
import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class Check:
    name: str
    status: str
    detail: str


def version(dist: str) -> str | None:
    try:
        return md.version(dist)
    except md.PackageNotFoundError:
        return None


def import_check(module: str) -> Check:
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            mod = importlib.import_module(module)
        detail = getattr(mod, "__file__", "imported")
        captured = " | ".join(line.strip() for line in out.getvalue().splitlines()[:3] if line.strip())
        if captured:
            detail = f"{detail}; import messages: {captured}"
        return Check(f"import:{module}", "PASS", detail)
    except Exception as exc:  # noqa: BLE001 - diagnostic helper
        captured = " | ".join(line.strip() for line in out.getvalue().splitlines()[:3] if line.strip())
        suffix = f"; messages: {captured}" if captured else ""
        return Check(f"import:{module}", "FAIL", f"{type(exc).__name__}: {exc}{suffix}")


def cuda_check() -> Check:
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            import torch

        if not torch.cuda.is_available():
            return Check("cuda", "WARN", "torch imported but CUDA is not available")
        name = torch.cuda.get_device_name(0)
        cap = torch.cuda.get_device_capability(0)
        torch.empty((1,), device="cuda")
        return Check("cuda", "PASS", f"{torch.cuda.device_count()} device(s); first={name}; capability={cap}")
    except Exception as exc:  # noqa: BLE001
        captured = " | ".join(line.strip() for line in out.getvalue().splitlines()[:3] if line.strip())
        suffix = f"; messages: {captured}" if captured else ""
        return Check("cuda", "FAIL", f"{type(exc).__name__}: {exc}{suffix}")


def optional_import(module: str, feature: str) -> Check:
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            importlib.import_module(module)
        captured = " | ".join(line.strip() for line in out.getvalue().splitlines()[:3] if line.strip())
        suffix = f"; messages: {captured}" if captured else ""
        return Check(feature, "PASS", f"{module} imports{suffix}")
    except Exception as exc:  # noqa: BLE001
        captured = " | ".join(line.strip() for line in out.getvalue().splitlines()[:3] if line.strip())
        suffix = f"; messages: {captured}" if captured else ""
        return Check(feature, "WARN", f"{module} unavailable: {type(exc).__name__}: {exc}{suffix}")


def run_help(module: str, timeout: int) -> Check:
    cmd = [sys.executable, "-m", module, "--help"]
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)
    except Exception as exc:  # noqa: BLE001
        return Check(f"help:{module}", "FAIL", f"{type(exc).__name__}: {exc}")
    if proc.returncode == 0:
        first = (proc.stdout or proc.stderr).strip().splitlines()[:2]
        return Check(f"help:{module}", "PASS", " | ".join(first))
    err = (proc.stderr or proc.stdout).strip().splitlines()[:4]
    return Check(f"help:{module}", "FAIL", " | ".join(err))


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe an installed XTuner environment without side effects.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument("--no-cuda", action="store_true", help="Skip torch CUDA allocation probe.")
    parser.add_argument("--check-sft-help", action="store_true", help="Run python -m xtuner.v1.train.cli.sft --help.")
    parser.add_argument("--check-rl-help", action="store_true", help="Run python -m xtuner.v1.train.cli.rl --help.")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout seconds for CLI help checks.")
    args = parser.parse_args()

    checks: list[Check] = []
    dists = {name: version(name) for name in ["xtuner", "torch", "transformers", "ray"]}
    checks.append(Check("distribution:xtuner", "PASS" if dists["xtuner"] else "FAIL", str(dists["xtuner"])))
    for module in ["xtuner", "xtuner.v1", "xtuner.v1.utils", "xtuner.v1.datasets.config"]:
        checks.append(import_check(module))
    if not args.no_cuda:
        checks.append(cuda_check())
    checks.extend(
        [
            optional_import("flash_attn", "optional:flash-attn"),
            optional_import("bitsandbytes", "optional:bitsandbytes"),
            optional_import("ray", "optional:ray"),
        ]
    )
    if args.check_sft_help:
        checks.append(run_help("xtuner.v1.train.cli.sft", args.timeout))
    if args.check_rl_help:
        checks.append(run_help("xtuner.v1.train.cli.rl", args.timeout))

    result: dict[str, Any] = {"python": sys.version.split()[0], "distributions": dists, "checks": [asdict(c) for c in checks]}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Python: {result['python']}")
        for name, value in dists.items():
            print(f"{name}: {value}")
        for check in checks:
            print(f"[{check.status}] {check.name}: {check.detail}")
    return 1 if any(c.status == "FAIL" for c in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
