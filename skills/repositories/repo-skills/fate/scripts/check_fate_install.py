#!/usr/bin/env python3
"""Safe root FATE installation/runtime inspection helper.

This script imports packages, checks distribution versions, runs help commands,
and reports CPU/GPU/service surfaces. It does not start services, contact
FateFlow, upload data, launch training, or mutate the host.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from typing import Any, Sequence

EXPECTED = {
    "pyfate": "2.2.0",
    "fate_utils": "0.1.0",
    "fate_client": "2.2.0",
    "fate_flow": "2.2.0",
}

ROOT_IMPORTS = {
    "fate": "pyfate",
    "fate_utils": "fate_utils",
}

SERVICE_IMPORTS = {
    "fate_client": "fate_client",
    "fate_flow": "fate_flow",
}


def run_command(cmd: Sequence[str], timeout: int = 20) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)
    except FileNotFoundError:
        return {"ok": False, "returncode": 127, "error": f"command not found: {cmd[0]}"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "returncode": 124, "error": f"timeout after {timeout}s", "command": list(cmd)}
    output = (proc.stdout or "") + (proc.stderr or "")
    first_line = next((line.strip() for line in output.splitlines() if line.strip()), "")
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "first_line": first_line,
        "command": list(cmd),
    }


def dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def import_report(import_name: str, dist_name: str) -> dict[str, Any]:
    report: dict[str, Any] = {
        "import": import_name,
        "distribution": dist_name,
        "expected_version": EXPECTED.get(dist_name),
        "installed_version": dist_version(dist_name),
    }
    try:
        module = importlib.import_module(import_name)
        report["ok"] = True
        version_attr = getattr(module, "__version__", None)
        if version_attr is not None:
            report["module_version_attr"] = str(version_attr)
    except Exception as exc:  # pragma: no cover - diagnostic path
        report["ok"] = False
        report["error"] = f"{type(exc).__name__}: {exc}"
    expected = report.get("expected_version")
    installed = report.get("installed_version")
    if expected is not None and installed is not None and installed != expected:
        report["warning"] = f"installed {installed}, expected {expected}"
    return report


def package_reports(include_service: bool) -> list[dict[str, Any]]:
    reports = [import_report(import_name, dist) for import_name, dist in ROOT_IMPORTS.items()]
    if include_service:
        reports.extend(import_report(import_name, dist) for import_name, dist in SERVICE_IMPORTS.items())
    return reports


def setuptools_report() -> dict[str, Any]:
    report: dict[str, Any] = {"distribution": "setuptools", "installed_version": dist_version("setuptools")}
    try:
        importlib.import_module("pkg_resources")
        report["pkg_resources_import"] = "ok"
        report["ok"] = True
    except Exception as exc:  # pragma: no cover - diagnostic path
        report["pkg_resources_import"] = f"{type(exc).__name__}: {exc}"
        report["ok"] = False
        report["warning"] = "component discovery may fail without pkg_resources; install/pin setuptools"
    return report


def torch_report() -> dict[str, Any]:
    report: dict[str, Any] = {}
    try:
        import torch  # type: ignore

        report["ok"] = True
        report["version"] = getattr(torch, "__version__", None)
        report["cuda_available"] = bool(torch.cuda.is_available())
        report["cuda_device_count"] = int(torch.cuda.device_count()) if report["cuda_available"] else 0
    except Exception as exc:  # pragma: no cover - optional dependency path
        report["ok"] = False
        report["error"] = f"{type(exc).__name__}: {exc}"
    return report


def command_reports(include_service: bool) -> dict[str, Any]:
    reports: dict[str, Any] = {
        "python_m_fate_components_help": run_command([sys.executable, "-m", "fate.components", "--help"]),
        "python_m_fate_components_component_help": run_command(
            [sys.executable, "-m", "fate.components", "component", "--help"]
        ),
    }
    if include_service:
        reports["fate_flow_on_path"] = shutil.which("fate_flow")
        reports["pipeline_on_path"] = shutil.which("pipeline")
        reports["fate_flow_help"] = run_command(["fate_flow", "--help"])
        reports["pipeline_help"] = run_command(["pipeline", "--help"])
    return reports


def collect(include_service: bool) -> dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "packages": package_reports(include_service),
        "setuptools": setuptools_report(),
        "torch": torch_report(),
        "commands": command_reports(include_service),
        "notes": [
            "CPU inspection/runtime checks are the verified baseline.",
            "Service checks only inspect CLI presence/help; this helper does not start FateFlow or contact a service.",
            "Use sub-skill helpers for workflow-specific validation after this root check passes."
        ],
    }


def has_warning_or_failure(report: dict[str, Any], include_service: bool) -> bool:
    for package in report["packages"]:
        if not package.get("ok") or package.get("warning"):
            return True
    if not report["setuptools"].get("ok"):
        return True
    for key, value in report["commands"].items():
        if key.endswith("_on_path"):
            if include_service and not value:
                return True
            continue
        if isinstance(value, dict) and not value.get("ok"):
            return True
    return False


def print_text(report: dict[str, Any]) -> None:
    print("FATE root install/runtime check")
    print("=" * 32)
    print(f"Python: {report['python']}")
    print("\nPackages:")
    for package in report["packages"]:
        status = "ok" if package.get("ok") else "FAIL"
        version = package.get("installed_version")
        expected = package.get("expected_version")
        extra = f" (expected {expected})" if expected else ""
        if package.get("warning"):
            extra += f" - WARN: {package['warning']}"
        if package.get("error"):
            extra += f" - {package['error']}"
        print(f"- {package['import']} / {package['distribution']}: {status}, installed={version}{extra}")

    setuptools = report["setuptools"]
    print(
        f"- pkg_resources via setuptools {setuptools.get('installed_version')}: "
        f"{'ok' if setuptools.get('ok') else setuptools.get('pkg_resources_import')}"
    )

    torch = report["torch"]
    if torch.get("ok"):
        print(f"- torch: {torch.get('version')} cuda_available={torch.get('cuda_available')}")
    else:
        print(f"- torch: optional import failed: {torch.get('error')}")

    print("\nCommands:")
    for key, value in report["commands"].items():
        if key.endswith("_on_path"):
            print(f"- {key}: {value or 'not found'}")
        else:
            status = "ok" if value.get("ok") else "FAIL"
            detail = value.get("first_line") or value.get("error") or f"returncode={value.get('returncode')}"
            print(f"- {key}: {status} - {detail}")

    print("\nNotes:")
    for note in report["notes"]:
        print(f"- {note}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-service", action="store_true", help="also check fate_client/fate_flow imports and fate_flow/pipeline help commands")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument("--strict", action="store_true", help="exit nonzero if required checks fail or warnings are present")
    args = parser.parse_args(argv)

    report = collect(args.include_service)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)

    return 1 if args.strict and has_warning_or_failure(report, args.include_service) else 0


if __name__ == "__main__":
    raise SystemExit(main())
