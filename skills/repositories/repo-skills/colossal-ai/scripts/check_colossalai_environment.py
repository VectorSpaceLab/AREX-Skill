#!/usr/bin/env python3
"""Safe ColossalAI environment diagnostic."""
import argparse
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys


def run(cmd):
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20)
        return {"cmd": cmd, "returncode": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}
    except Exception as exc:
        return {"cmd": cmd, "error": f"{type(exc).__name__}: {exc}"}


def main():
    ap = argparse.ArgumentParser(description="Check ColossalAI import, PyTorch backend, and optional CLI parser availability.")
    ap.add_argument("--require-cuda", action="store_true", help="Return nonzero if PyTorch CUDA is unavailable.")
    ap.add_argument("--check-cli", action="store_true", help="Run safe CLI help parser checks.")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable lines.")
    args = ap.parse_args()
    report = {"python": sys.version.split()[0], "ok": True, "warnings": []}
    try:
        import colossalai
        report["colossalai_import"] = True
        report["colossalai_version"] = getattr(colossalai, "__version__", None)
        try:
            report["colossalai_distribution_version"] = metadata.version("colossalai")
        except metadata.PackageNotFoundError:
            report["warnings"].append("colossalai distribution metadata not found")
    except Exception as exc:
        report["ok"] = False
        report["colossalai_import"] = False
        report["colossalai_error"] = f"{type(exc).__name__}: {exc}"
    try:
        import torch
        report["torch_version"] = torch.__version__
        report["torch_cuda_version"] = getattr(torch.version, "cuda", None)
        report["cuda_available"] = bool(torch.cuda.is_available())
        report["cuda_device_count"] = int(torch.cuda.device_count()) if hasattr(torch, "cuda") else 0
        if torch.cuda.is_available():
            report["cuda_device_0"] = torch.cuda.get_device_name(0)
            report["cuda_capability_0"] = list(torch.cuda.get_device_capability(0))
            torch.empty((1,), device="cuda")
            report["cuda_tiny_allocation"] = True
        elif args.require_cuda:
            report["ok"] = False
            report["warnings"].append("--require-cuda was set but torch.cuda.is_available() is False")
    except Exception as exc:
        report["ok"] = False
        report["torch_error"] = f"{type(exc).__name__}: {exc}"
    if args.check_cli:
        exe = shutil.which("colossalai")
        report["colossalai_cli"] = exe is not None
        if exe:
            report["cli_checks"] = [run([exe, "--help"]), run([exe, "run", "--help"]), run([exe, "check", "--help"])]
            if any(c.get("returncode") not in (0, None) or c.get("error") for c in report["cli_checks"]):
                report["ok"] = False
        else:
            report["warnings"].append("colossalai console script not found on PATH")
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for key in sorted(k for k in report if k not in {"cli_checks", "warnings"}):
            print(f"{key}: {report[key]}")
        for warning in report.get("warnings", []):
            print(f"warning: {warning}")
        for check in report.get("cli_checks", []):
            print(f"cli {' '.join(check.get('cmd', []))}: {check.get('returncode', check.get('error'))}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
