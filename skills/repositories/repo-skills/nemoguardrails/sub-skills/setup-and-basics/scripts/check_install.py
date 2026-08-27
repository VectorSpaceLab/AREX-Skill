#!/usr/bin/env python3
"""Safe NeMo Guardrails installation checker.

This helper performs import and metadata checks only. It does not instantiate
rails, start servers, call model providers, download models, or write files.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import sys
from types import ModuleType
from typing import Any

PYTHON_MIN = (3, 10)
PYTHON_MAX_EXCLUSIVE = (3, 14)
DISTRIBUTION = "nemoguardrails"

CORE_SYMBOLS = [
    "Guardrails",
    "LLMRails",
    "RailsConfig",
    "ChatMessage",
    "LLMModel",
    "LLMResponse",
    "LLMResponseChunk",
    "register_provider",
    "set_default_framework",
    "get_default_framework",
]

TESTING_SYMBOLS = ["FakeLLMModel", "RecordingHTTPClient", "TestChat"]

EXTRA_MODULES = {
    "server": ["aiofiles", "fastapi", "openai", "starlette", "uvicorn", "watchdog"],
    "eval": ["pandas", "streamlit", "tornado", "tqdm"],
    "tracing": ["aiofiles", "opentelemetry"],
    "chat-ui": ["chainlit"],
    "sdd": ["presidio_analyzer", "presidio_anonymizer"],
    "jailbreak": ["yara"],
    "multilingual": ["fast_langdetect"],
    "gcp": ["google.cloud.language"],
}
EXTRA_MODULES["all"] = sorted({module for modules in EXTRA_MODULES.values() for module in modules})


def python_supported() -> bool:
    return PYTHON_MIN <= sys.version_info[:2] < PYTHON_MAX_EXCLUSIVE


def module_version(module: ModuleType) -> str | None:
    value = getattr(module, "__version__", None)
    if isinstance(value, str):
        return value
    return None


def install_hint(module_name: str, extra: str | None) -> str:
    if extra:
        return f"Install the related extra with: python -m pip install 'nemoguardrails[{extra}]'"
    package_guess = module_name.split(".")[0].replace("_", "-")
    return f"Install the missing optional package if the requested feature needs it: python -m pip install {package_guess}"


def check_module(module_name: str, *, required: bool, extra: str | None = None) -> dict[str, Any]:
    record: dict[str, Any] = {
        "kind": "module",
        "name": module_name,
        "required": required,
        "ok": False,
    }
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
        record["suggestion"] = install_hint(module_name, extra)
        return record
    except Exception as exc:  # defensive: import-time config errors should be visible
        record["error"] = f"{type(exc).__name__}: {exc}"
        record["suggestion"] = "The module was found but failed during import; inspect package versions and environment configuration."
        return record

    record["ok"] = True
    version = module_version(module)
    if version:
        record["version"] = version
    return record


def check_symbol(module: ModuleType, symbol: str, *, group: str) -> dict[str, Any]:
    record = {
        "kind": "symbol",
        "group": group,
        "name": symbol,
        "required": True,
        "ok": hasattr(module, symbol),
    }
    if not record["ok"]:
        record["error"] = f"Missing expected public symbol: {symbol}"
    return record


def package_metadata() -> dict[str, Any]:
    try:
        md = metadata.metadata(DISTRIBUTION)
    except metadata.PackageNotFoundError:
        return {"distribution": DISTRIBUTION, "installed": False}
    return {
        "distribution": DISTRIBUTION,
        "installed": True,
        "version": md.get("Version"),
        "requires_python": md.get("Requires-Python"),
    }


def parse_module_spec(spec: str) -> tuple[str, str | None]:
    module_name, sep, extra = spec.partition(":")
    module_name = module_name.strip()
    extra = extra.strip() if sep else None
    if not module_name:
        raise argparse.ArgumentTypeError("--check-module requires MODULE or MODULE:EXTRA")
    return module_name, extra or None


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    report: dict[str, Any] = {
        "python": {
            "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "supported": python_supported(),
            "requires": ">=3.10,<3.14",
        },
        "package_metadata": package_metadata(),
        "checks": [],
    }

    top_module: ModuleType | None = None
    top_import = check_module("nemoguardrails", required=True)
    report["checks"].append(top_import)
    if top_import["ok"]:
        top_module = importlib.import_module("nemoguardrails")
        report["package_import"] = {"version": getattr(top_module, "__version__", None)}
        for symbol in CORE_SYMBOLS:
            report["checks"].append(check_symbol(top_module, symbol, group="nemoguardrails"))

    testing_import = check_module("nemoguardrails.testing", required=True)
    report["checks"].append(testing_import)
    if testing_import["ok"]:
        testing_module = importlib.import_module("nemoguardrails.testing")
        for symbol in TESTING_SYMBOLS:
            report["checks"].append(check_symbol(testing_module, symbol, group="nemoguardrails.testing"))

    if args.check_cli and not args.skip_cli:
        report["checks"].append(check_module("nemoguardrails.__main__", required=True))
        report["checks"].append(check_module("nemoguardrails.cli", required=True))

    requested_modules: list[tuple[str, str | None]] = []
    for extra in args.check_extra:
        for module_name in EXTRA_MODULES[extra]:
            requested_modules.append((module_name, None if extra == "all" else extra))
    requested_modules.extend(args.check_module)

    seen: set[tuple[str, str | None]] = set()
    for module_name, extra in requested_modules:
        key = (module_name, extra)
        if key in seen:
            continue
        seen.add(key)
        report["checks"].append(check_module(module_name, required=True, extra=extra))

    report["ok"] = report["python"]["supported"] and all(
        check.get("ok", False) for check in report["checks"] if check.get("required")
    )
    return report


def print_text(report: dict[str, Any]) -> None:
    status = "OK" if report["ok"] else "FAILED"
    print(f"NeMo Guardrails install check: {status}")
    py = report["python"]
    print(f"Python: {py['version']} (supported {py['requires']}: {py['supported']})")

    md = report["package_metadata"]
    if md.get("installed"):
        print(f"Distribution: {md['distribution']} {md.get('version') or 'unknown'}")
        if md.get("requires_python"):
            print(f"Requires-Python: {md['requires_python']}")
    else:
        print(f"Distribution metadata not found for {md['distribution']}")

    imported_version = report.get("package_import", {}).get("version")
    if imported_version:
        print(f"Imported package version: {imported_version}")

    for check in report["checks"]:
        marker = "PASS" if check.get("ok") else "FAIL"
        required = "required" if check.get("required") else "optional"
        label = check.get("group", check.get("kind", "check"))
        print(f"[{marker}] {label}: {check['name']} ({required})")
        if not check.get("ok"):
            if check.get("error"):
                print(f"  error: {check['error']}")
            if check.get("suggestion"):
                print(f"  suggestion: {check['suggestion']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Safely verify NeMo Guardrails package imports, metadata, optional modules, and CLI importability."
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    parser.add_argument(
        "--check-module",
        action="append",
        default=[],
        type=parse_module_spec,
        metavar="MODULE[:EXTRA]",
        help="Import an additional optional module. Add :EXTRA to print a nemoguardrails[extra] hint on failure.",
    )
    parser.add_argument(
        "--check-extra",
        action="append",
        default=[],
        choices=sorted(EXTRA_MODULES),
        help="Import-check representative modules for a NeMo Guardrails extra. May be repeated.",
    )
    parser.add_argument(
        "--check-cli",
        action="store_true",
        help="Also import-check nemoguardrails.__main__ and nemoguardrails.cli without running commands.",
    )
    parser.add_argument(
        "--skip-cli",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)

    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
