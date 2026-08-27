#!/usr/bin/env python3
"""Quick install and export doctor for the PhySO repo skill."""

from __future__ import annotations

import argparse
import json
from contextlib import redirect_stderr, redirect_stdout
from importlib import import_module
from io import StringIO
from typing import Any

REQUIRED_ROOT_EXPORTS = ("SR", "ClassSR", "read_pareto_csv", "read_pareto_pkl", "load_expr")
REQUIRED_TOOLKIT_EXPORTS = ("get_library", "sample_random_expressions")
REQUIRED_STACK_MODULES = ("torch", "numpy", "sympy", "pandas", "matplotlib", "sklearn")


def _import_version(name: str) -> tuple[Any | None, str | None, str | None]:
    try:
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            module = import_module(name)
    except Exception as exc:  # pragma: no cover - surfaced in CLI output
        return None, None, str(exc)
    return module, getattr(module, "__version__", "unknown"), None


def _human_report(report: dict[str, Any]) -> str:
    lines = ["PhySO doctor: PASS" if report["status"] == "ok" else "PhySO doctor: FAIL"]
    lines.append(f"  physo: {report.get('physo_version', 'unknown')}")
    lines.append(f"  torch: {report.get('torch_version', 'missing')} (cuda_available={report.get('cuda_available', 'unknown')})")
    if report.get("stack_versions"):
        stack = ", ".join(f"{k}={v}" for k, v in report["stack_versions"].items())
        lines.append(f"  scientific stack: {stack}")
    if report.get("root_exports"):
        lines.append("  root exports: " + ", ".join(name for name, present in report["root_exports"].items() if present))
    if report.get("toolkit_exports"):
        lines.append("  toolkit exports: " + ", ".join(name for name, present in report["toolkit_exports"].items() if present))
    if report.get("missing"):
        lines.append("  missing: " + "; ".join(report["missing"]))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the PhySO install and key public exports.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    args = parser.parse_args()

    report: dict[str, Any] = {
        "status": "ok",
        "physo_version": None,
        "root_exports": {},
        "toolkit_exports": {},
        "stack_versions": {},
        "missing": [],
    }

    physo, physo_version, err = _import_version("physo")
    if err:
        report["status"] = "fail"
        report["missing"].append(f"physo import: {err}")
        print(json.dumps(report, indent=2, sort_keys=True) if args.json else _human_report(report))
        return 1

    report["physo_version"] = physo_version
    report["root_exports"] = {name: hasattr(physo, name) for name in REQUIRED_ROOT_EXPORTS}
    missing_root = [name for name, present in report["root_exports"].items() if not present]
    if missing_root:
        report["status"] = "fail"
        report["missing"].append("root exports: " + ", ".join(missing_root))

    toolkit, _, err = _import_version("physo.toolkit")
    if err:
        report["status"] = "fail"
        report["missing"].append(f"physo.toolkit import: {err}")
    else:
        report["toolkit_exports"] = {name: hasattr(toolkit, name) for name in REQUIRED_TOOLKIT_EXPORTS}
        missing_toolkit = [name for name, present in report["toolkit_exports"].items() if not present]
        if missing_toolkit:
            report["status"] = "fail"
            report["missing"].append("toolkit exports: " + ", ".join(missing_toolkit))

    for modname in REQUIRED_STACK_MODULES:
        module, version, err = _import_version(modname)
        if err:
            report["status"] = "fail"
            report["missing"].append(f"{modname} import: {err}")
        else:
            report["stack_versions"][modname] = version
            if modname == "torch":
                try:
                    report["cuda_available"] = bool(module.cuda.is_available())
                except Exception:
                    report["cuda_available"] = "unknown"
                report["torch_version"] = version

    print(json.dumps(report, indent=2, sort_keys=True) if args.json else _human_report(report))
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
