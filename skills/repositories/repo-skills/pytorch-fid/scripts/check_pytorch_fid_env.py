#!/usr/bin/env python3
"""Safely inspect a pytorch-fid runtime environment.

This helper checks imports, package metadata, CLI help, torch/torchvision
versions, and CUDA availability. It deliberately does not construct InceptionV3,
load weights, read image inputs, or trigger network downloads.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from importlib import metadata
from typing import Any, Dict, List, Tuple


def _module_import(name: str) -> Tuple[bool, str | None]:
    try:
        importlib.import_module(name)
        return True, None
    except Exception as exc:  # pragma: no cover - environment dependent
        return False, f"{type(exc).__name__}: {exc}"


def _distribution_version(dist_name: str) -> Tuple[str | None, str | None]:
    try:
        return metadata.version(dist_name), None
    except metadata.PackageNotFoundError:
        return None, "distribution not found"
    except Exception as exc:  # pragma: no cover - environment dependent
        return None, f"{type(exc).__name__}: {exc}"


def _attribute_version(module_name: str) -> Tuple[str | None, str | None]:
    try:
        module = importlib.import_module(module_name)
        return getattr(module, "__version__", None), None
    except Exception as exc:  # pragma: no cover - environment dependent
        return None, f"{type(exc).__name__}: {exc}"


def _run_cli_help() -> Dict[str, Any]:
    command = [sys.executable, "-m", "pytorch_fid", "--help"]
    try:
        proc = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
    except Exception as exc:  # pragma: no cover - environment dependent
        return {
            "command": command,
            "ok": False,
            "returncode": None,
            "error": f"{type(exc).__name__}: {exc}",
        }

    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    expected_flags = ["--batch-size", "--num-workers", "--device", "--dims", "--save-stats"]
    missing_flags = [flag for flag in expected_flags if flag not in combined]
    return {
        "command": command,
        "ok": proc.returncode == 0 and not missing_flags,
        "returncode": proc.returncode,
        "missing_expected_flags": missing_flags,
        "stdout_first_line": (proc.stdout.splitlines()[0] if proc.stdout.splitlines() else ""),
        "stderr_first_line": (proc.stderr.splitlines()[0] if proc.stderr.splitlines() else ""),
    }


def _torch_info() -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "torch_import_ok": False,
        "torch_version": None,
        "torch_error": None,
        "torchvision_import_ok": False,
        "torchvision_version": None,
        "torchvision_error": None,
        "cuda_available": None,
        "cuda_device_count": None,
    }

    try:
        torch = importlib.import_module("torch")
        info["torch_import_ok"] = True
        info["torch_version"] = getattr(torch, "__version__", None)
        try:
            info["cuda_available"] = bool(torch.cuda.is_available())
            info["cuda_device_count"] = int(torch.cuda.device_count())
        except Exception as exc:  # pragma: no cover - environment dependent
            info["cuda_error"] = f"{type(exc).__name__}: {exc}"
    except Exception as exc:  # pragma: no cover - environment dependent
        info["torch_error"] = f"{type(exc).__name__}: {exc}"

    try:
        torchvision = importlib.import_module("torchvision")
        info["torchvision_import_ok"] = True
        info["torchvision_version"] = getattr(torchvision, "__version__", None)
    except Exception as exc:  # pragma: no cover - environment dependent
        info["torchvision_error"] = f"{type(exc).__name__}: {exc}"

    return info


def build_report(run_cli_help: bool = True) -> Dict[str, Any]:
    dist_version, dist_error = _distribution_version("pytorch-fid")
    import_checks = {}
    for module_name in ["pytorch_fid", "pytorch_fid.fid_score", "pytorch_fid.inception"]:
        ok, error = _module_import(module_name)
        import_checks[module_name] = {"ok": ok, "error": error}

    package_version, package_version_error = _attribute_version("pytorch_fid")
    console_script = shutil.which("pytorch-fid") is not None

    report: Dict[str, Any] = {
        "package": "pytorch-fid",
        "distribution_version": dist_version,
        "distribution_error": dist_error,
        "pytorch_fid_version_attribute": package_version,
        "pytorch_fid_version_attribute_error": package_version_error,
        "imports": import_checks,
        "console_script_on_path": console_script,
        "cli_help": _run_cli_help() if run_cli_help else {"skipped": True},
        "torch": _torch_info(),
        "notes": [
            "This helper does not construct InceptionV3 or download weights.",
            "For torch builds that warn or fail with NumPy 2, use a NumPy 1.x runtime such as numpy<2.",
        ],
    }

    required_ok = bool(dist_version) and all(item["ok"] for item in import_checks.values())
    cli_ok = True if not run_cli_help else bool(report["cli_help"].get("ok"))
    report["ok"] = bool(required_ok and cli_ok and report["torch"]["torch_import_ok"] and report["torch"]["torchvision_import_ok"])
    return report


def _print_text(report: Dict[str, Any]) -> None:
    status = "OK" if report["ok"] else "ISSUES"
    print(f"pytorch-fid environment check: {status}")
    print(f"distribution version: {report['distribution_version'] or 'unavailable'}")
    if report.get("distribution_error"):
        print(f"distribution issue: {report['distribution_error']}")
    print(f"pytorch_fid __version__: {report['pytorch_fid_version_attribute'] or 'unavailable'}")
    print(f"console script on PATH: {report['console_script_on_path']}")

    print("imports:")
    for name, item in report["imports"].items():
        marker = "OK" if item["ok"] else "FAIL"
        print(f"  {marker} {name}" + (f" ({item['error']})" if item.get("error") else ""))

    cli = report["cli_help"]
    if cli.get("skipped"):
        print("cli help: skipped")
    else:
        marker = "OK" if cli.get("ok") else "FAIL"
        print(f"cli help: {marker} returncode={cli.get('returncode')}")
        if cli.get("missing_expected_flags"):
            print("  missing expected flags: " + ", ".join(cli["missing_expected_flags"]))
        if cli.get("error"):
            print(f"  error: {cli['error']}")
        if cli.get("stderr_first_line"):
            print(f"  stderr first line: {cli['stderr_first_line']}")

    torch_info = report["torch"]
    print(f"torch: {'OK' if torch_info['torch_import_ok'] else 'FAIL'} {torch_info.get('torch_version') or ''}".rstrip())
    if torch_info.get("torch_error"):
        print(f"  torch error: {torch_info['torch_error']}")
    print(f"torchvision: {'OK' if torch_info['torchvision_import_ok'] else 'FAIL'} {torch_info.get('torchvision_version') or ''}".rstrip())
    if torch_info.get("torchvision_error"):
        print(f"  torchvision error: {torch_info['torchvision_error']}")
    print(f"cuda available: {torch_info.get('cuda_available')}")
    print(f"cuda device count: {torch_info.get('cuda_device_count')}")
    for note in report.get("notes", []):
        print(f"note: {note}")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Safely check pytorch-fid imports, CLI help, torch/torchvision, and CUDA availability."
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    parser.add_argument(
        "--skip-cli-help",
        action="store_true",
        help="Skip the subprocess `python -m pytorch_fid --help` check.",
    )
    args = parser.parse_args(argv)

    report = build_report(run_cli_help=not args.skip_cli_help)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
