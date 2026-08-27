#!/usr/bin/env python3
"""Check installed Giskard split-package imports without provider calls.

Prerequisites: Python 3.12+ with the desired Giskard packages installed.
Examples:
  python scripts/check_giskard_imports.py
  python scripts/check_giskard_imports.py --json
  python scripts/check_giskard_imports.py --require-scan

The script is safe for diagnostics: it sets telemetry opt-out before importing
Giskard packages, performs no network calls, never invokes provider SDK methods,
and does not require a source repository checkout.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import importlib.util
import json
import os
import sys
from dataclasses import dataclass
from typing import Any

# Set telemetry opt-out before importing any giskard package.
os.environ.setdefault("DO_NOT_TRACK", "1")
os.environ.setdefault("GISKARD_TELEMETRY_DISABLED", "1")
os.environ.setdefault("GISKARD_CHECKS_DISABLE_RICH_PRETTY", "1")

DISTRIBUTIONS = [
    "giskard",
    "giskard-core",
    "giskard-llm",
    "giskard-agents",
    "giskard-checks",
    "giskard-scan",
]

MODULES = [
    ("giskard.core", "giskard-core", True),
    ("giskard.llm", "giskard-llm", True),
    ("giskard.agents", "giskard-agents", True),
    ("giskard.checks", "giskard-checks", True),
    ("giskard.scan", "giskard-scan", False),
]

OPTIONAL_IMPORTS = {
    "openai": "giskard-llm[openai] or giskard[openai]",
    "google.genai": "giskard-llm[google] or giskard[google]",
    "anthropic": "giskard-llm[anthropic] or giskard[anthropic]",
    "litellm": "giskard-agents[litellm] or giskard[litellm]",
    "regorus": "giskard-checks[regorus] or giskard[regorus]",
    "garak": "giskard-scan[garak] or giskard[garak]",
    "deepteam": "giskard-scan[deepteam] or giskard[deepteam]",
}


@dataclass
class ImportResult:
    module: str
    required: bool
    ok: bool
    version: str | None = None
    error: str | None = None


def _dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _import_module(module: str, dist: str, required: bool) -> ImportResult:
    try:
        imported = importlib.import_module(module)
    except Exception as exc:  # pragma: no cover - diagnostic branch
        return ImportResult(
            module=module,
            required=required,
            ok=False,
            version=_dist_version(dist),
            error=f"{type(exc).__name__}: {exc}",
        )
    return ImportResult(
        module=module,
        required=required,
        ok=True,
        version=getattr(imported, "__version__", None) or _dist_version(dist),
    )


def _build_report(require_scan: bool) -> dict[str, Any]:
    modules = []
    for module, dist, default_required in MODULES:
        required = default_required or (module == "giskard.scan" and require_scan)
        modules.append(_import_module(module, dist, required))

    optional = {
        name: {
            "available": importlib.util.find_spec(name) is not None,
            "install_hint": hint,
        }
        for name, hint in OPTIONAL_IMPORTS.items()
    }

    python_ok = sys.version_info >= (3, 12)
    return {
        "ok": python_ok and all(result.ok or not result.required for result in modules),
        "python": {
            "version": sys.version.split()[0],
            "requires": ">=3.12",
            "ok": python_ok,
        },
        "distributions": {name: _dist_version(name) for name in DISTRIBUTIONS},
        "imports": [result.__dict__ for result in modules],
        "optional": optional,
        "notes": [
            "Import namespace is giskard.<sublib>, not giskard_checks or giskard_scan.",
            "Optional provider/scanner packages can be absent until their workflows are selected.",
            "This script does not verify live provider credentials, remote datasets, or third-party scanner execution.",
        ],
    }


def _print_text(report: dict[str, Any]) -> None:
    print("Giskard installed-package import check")
    print(f"Python: {report['python']['version']} (requires {report['python']['requires']})")
    if not report["python"]["ok"]:
        print("ERROR: Python 3.12 or newer is required.")

    print("\nDistributions:")
    for name, version in report["distributions"].items():
        print(f"  {name}: {version or 'not installed'}")

    print("\nImports:")
    for item in report["imports"]:
        status = "ok" if item["ok"] else "FAILED"
        required = "required" if item["required"] else "optional"
        suffix = f" ({item['error']})" if item.get("error") else ""
        print(f"  {item['module']}: {status} [{required}] version={item.get('version') or 'unknown'}{suffix}")

    print("\nOptional dependency availability:")
    for name, item in report["optional"].items():
        status = "available" if item["available"] else "missing"
        print(f"  {name}: {status}; install hint: {item['install_hint']}")

    print("\nNotes:")
    for note in report["notes"]:
        print(f"  - {note}")

    print("\nOverall:", "OK" if report["ok"] else "FAILED")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--require-scan",
        action="store_true",
        help="Treat giskard.scan as required instead of optional.",
    )
    args = parser.parse_args()

    report = _build_report(require_scan=args.require_scan)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
