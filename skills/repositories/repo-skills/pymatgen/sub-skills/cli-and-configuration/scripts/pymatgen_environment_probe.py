#!/usr/bin/env python3
"""Redacted pymatgen import/version and console entry-point probe."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import os
import shutil
import sys
from pathlib import Path

DISTRIBUTIONS = ("pymatgen", "pymatgen-core")
MODULES = (
    "pymatgen",
    "pymatgen.cli.pmg",
    "pymatgen.cli.pmg_config",
    "pymatgen.cli.pmg_structure",
    "pymatgen.cli.pmg_plot",
    "pymatgen.cli.pmg_analyze",
    "pymatgen.cli.pmg_potcar",
    "pymatgen.cli.get_environment",
    "pymatgen.ext.matproj",
)
CONSOLE_SCRIPTS = ("pmg", "get_environment", "feff_plot_cross_section", "feff_plot_dos")
SENSITIVE_ENV_NAMES = ("PMG_MAPI_KEY", "PMG_VASP_PSP_DIR", "PMG_CP2K_DATA_DIR", "PMG_CONFIG_FILE")


def distribution_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not-installed"


def module_status(name: str) -> dict[str, object]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - concise symptom without traceback or paths
        return {"module": name, "ok": False, "status": f"ERROR {type(exc).__name__}: {exc}"}

    version = getattr(module, "__version__", None)
    return {"module": name, "ok": True, "status": f"ok version={version}" if version else "ok"}


def entry_point_targets() -> dict[str, str]:
    targets: dict[str, str] = {}
    try:
        scripts = metadata.entry_points(group="console_scripts")
    except TypeError:
        scripts = metadata.entry_points().get("console_scripts", ())  # type: ignore[union-attr]
    for entry_point in scripts:
        if entry_point.name in CONSOLE_SCRIPTS:
            targets[entry_point.name] = entry_point.value
    return targets


def find_script(name: str) -> str | None:
    path = shutil.which(name)
    if path:
        return path
    script_dir = Path(sys.executable).resolve().parent
    candidate = script_dir / name
    if candidate.exists():
        return str(candidate)
    windows_candidate = script_dir / f"{name}.exe"
    if windows_candidate.exists():
        return str(windows_candidate)
    return None


def console_status(name: str, targets: dict[str, str], reveal_paths: bool) -> dict[str, object]:
    path = find_script(name)
    entry_target = targets.get(name, "entry-point-not-advertised")
    result: dict[str, object] = {"script": name, "found": path is not None, "target": entry_target}
    if path and reveal_paths:
        result["path"] = path
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check pymatgen distributions, importable modules, console entry points, and selected "
            "environment-variable presence. Local paths and secret values are redacted unless "
            "--reveal-paths is set. This script performs no setup, network calls, or config mutation."
        )
    )
    parser.add_argument("--reveal-paths", action="store_true", help="Print local console-script paths for private debugging.")
    parser.add_argument("--modules", nargs="*", default=list(MODULES), help="Import modules to check.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    args = parser.parse_args(argv)

    targets = entry_point_targets()
    modules = [module_status(module_name) for module_name in args.modules]
    consoles = [console_status(script, targets, args.reveal_paths) for script in CONSOLE_SCRIPTS]
    sensitive_env = {env_name: ("set" if env_name in os.environ else "unset") for env_name in SENSITIVE_ENV_NAMES}
    distributions = {dist: distribution_version(dist) for dist in DISTRIBUTIONS}
    report = {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "distributions": distributions,
        "imports": modules,
        "console_scripts": consoles,
        "sensitive_environment_variables": sensitive_env,
        "network_calls": False,
        "config_mutation": False,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("## Python")
        print(f"version={report['python_version']}")

        print("\n## Distributions")
        for dist, version in distributions.items():
            print(f"{dist}: {version}")

        print("\n## Imports")
        for item in modules:
            print(f"{item['module']}: {item['status']}")

        print("\n## Console Scripts")
        for item in consoles:
            state = "on-PATH-or-env-bin" if item["found"] else "missing"
            if args.reveal_paths and "path" in item:
                print(f"{item['script']}: {state} path={item['path']} target={item['target']}")
            else:
                print(f"{item['script']}: {state} target={item['target']}")

        print("\n## Sensitive Environment Variables")
        for env_name, state in sensitive_env.items():
            print(f"{env_name}: {state}")

    import_failures = sum(1 for item in modules if not item["ok"])
    missing_scripts = sum(1 for item in consoles if not item["found"])
    if import_failures:
        return 2
    if missing_scripts:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
