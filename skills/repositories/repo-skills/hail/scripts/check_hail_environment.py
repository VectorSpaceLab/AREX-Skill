#!/usr/bin/env python3
"""Read-only diagnostics for an installed Hail environment.

The script checks import resolution, package metadata, hailctl availability,
Java/PySpark signals, and packaged Hail resources without running hl.init by
default. It is safe to run from arbitrary current working directories.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import importlib.resources as resources
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_command(command: list[str], timeout: int = 10) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
            "timed_out": False,
        }
    except FileNotFoundError as error:
        return {
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": str(error),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as error:
        return {
            "command": command,
            "returncode": None,
            "stdout": (error.stdout or "").strip() if isinstance(error.stdout, str) else "",
            "stderr": (error.stderr or "").strip() if isinstance(error.stderr, str) else "",
            "timed_out": True,
        }


def module_facts(name: str) -> dict[str, Any]:
    facts: dict[str, Any] = {"name": name, "ok": False}
    try:
        module = importlib.import_module(name)
    except Exception as error:  # noqa: BLE001 - diagnostic should capture any import failure
        facts["error"] = f"{type(error).__name__}: {error}"
        return facts

    facts["ok"] = True
    facts["file"] = getattr(module, "__file__", None)
    facts["path"] = [str(path) for path in getattr(module, "__path__", [])]
    facts["version"] = getattr(module, "__version__", None)
    facts["pip_version"] = getattr(module, "__pip_version__", None)
    return facts


def package_resource_facts() -> dict[str, Any]:
    facts: dict[str, Any] = {}
    try:
        hail_files = resources.files("hail")
        facts["hail_backend_jar"] = str(hail_files / "backend" / "hail-all-spark.jar")
        facts["hail_backend_jar_exists"] = (hail_files / "backend" / "hail-all-spark.jar").is_file()
        facts["experimental_datasets_json_exists"] = (hail_files / "experimental" / "datasets.json").is_file()
    except Exception as error:  # noqa: BLE001
        facts["resource_error"] = f"{type(error).__name__}: {error}"
    return facts


def detect_shadowing(import_facts: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    cwd = Path.cwd().resolve()
    hail_file = import_facts.get("hail", {}).get("file")
    hail_path = import_facts.get("hail", {}).get("path") or []
    if hail_file:
        try:
            if Path(hail_file).resolve().is_relative_to(cwd):
                warnings.append("imported hail from under the current working directory; a source tree may be shadowing the installed package")
        except ValueError:
            pass
    for path in hail_path:
        try:
            if Path(path).resolve().is_relative_to(cwd):
                warnings.append("hail namespace path is under the current working directory; use a neutral directory for installed-package checks")
        except ValueError:
            pass
    return warnings


def collect(args: argparse.Namespace) -> dict[str, Any]:
    import_facts = {
        "hail": module_facts("hail"),
        "hailtop": module_facts("hailtop"),
    }
    report: dict[str, Any] = {
        "python": {
            "executable": sys.executable if args.show_executable else "omitted",
            "version": sys.version.split()[0],
            "cwd": str(Path.cwd()) if args.show_cwd else "omitted",
        },
        "distribution": {},
        "imports": import_facts,
        "resources": package_resource_facts(),
        "commands": {},
        "warnings": detect_shadowing(import_facts),
    }

    try:
        dist = metadata.distribution("hail")
        report["distribution"] = {
            "version": dist.version,
            "requires": sorted(dist.requires or []),
            "entry_points": [entry.name for entry in dist.entry_points if entry.group == "console_scripts"],
        }
    except Exception as error:  # noqa: BLE001
        report["distribution"] = {"error": f"{type(error).__name__}: {error}"}

    executable_dir = Path(sys.executable).resolve().parent
    candidate_hailctl = executable_dir / ("hailctl.exe" if os.name == "nt" else "hailctl")
    hailctl = shutil.which("hailctl") or (str(candidate_hailctl) if candidate_hailctl.exists() else None)
    report["commands"]["hailctl_path"] = hailctl if hailctl and args.show_executable else ("found" if hailctl else "missing")
    if hailctl:
        report["commands"]["hailctl_help"] = run_command([hailctl, "--help"], timeout=args.timeout)
        report["commands"]["hailctl_version"] = run_command([hailctl, "version"], timeout=args.timeout)
    else:
        report["commands"]["hailctl_module_help"] = run_command([sys.executable, "-m", "hailtop.hailctl", "--help"], timeout=args.timeout)

    java = shutil.which("java")
    report["commands"]["java_path"] = java or "missing"
    if java:
        report["commands"]["java_version"] = run_command([java, "-version"], timeout=args.timeout)

    try:
        pyspark = importlib.import_module("pyspark")
        report["imports"]["pyspark"] = {
            "ok": True,
            "version": getattr(pyspark, "__version__", None),
            "file": getattr(pyspark, "__file__", None),
        }
    except Exception as error:  # noqa: BLE001
        report["imports"]["pyspark"] = {"ok": False, "error": f"{type(error).__name__}: {error}"}

    if args.try_local_init:
        try:
            import hail as hl

            hl.init(backend="local", quiet=True, idempotent=True)
            backend = type(hl.current_backend()).__name__
            hl.stop()
            report["local_init"] = {"ok": True, "backend": backend}
        except Exception as error:  # noqa: BLE001
            report["local_init"] = {"ok": False, "error": f"{type(error).__name__}: {error}"}

    return report


def print_human(report: dict[str, Any]) -> None:
    print("Hail environment diagnostic")
    print(f"Python: {report['python']['version']}")
    print(f"Hail distribution: {report['distribution'].get('version', report['distribution'].get('error', 'unknown'))}")
    for name, facts in report["imports"].items():
        if isinstance(facts, dict):
            status = "ok" if facts.get("ok") else "fail"
            version = facts.get("version") or facts.get("pip_version") or ""
            print(f"Import {name}: {status} {version}".rstrip())
            if facts.get("error"):
                print(f"  {facts['error']}")
    print(f"hailctl: {report['commands'].get('hailctl_path')}")
    print(f"java: {report['commands'].get('java_path')}")
    resources_report = report.get("resources", {})
    print(f"Packaged Hail JAR present: {resources_report.get('hail_backend_jar_exists')}")
    for warning in report.get("warnings", []):
        print(f"WARNING: {warning}")
    if "local_init" in report:
        print(f"Local init: {'ok' if report['local_init'].get('ok') else 'fail'}")
        if report["local_init"].get("error"):
            print(f"  {report['local_init']['error']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only Hail environment diagnostic.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--timeout", type=int, default=10, help="Timeout seconds for external commands.")
    parser.add_argument("--try-local-init", action="store_true", help="Also attempt hl.init(backend='local'); may start Java/Spark.")
    parser.add_argument("--show-executable", action="store_true", help="Include the current Python executable path in private diagnostic output.")
    parser.add_argument("--show-cwd", action="store_true", help="Include the current working directory in private diagnostic output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = collect(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    failures = [name for name in ("hail", "hailtop") if not report["imports"].get(name, {}).get("ok")]
    if failures:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
