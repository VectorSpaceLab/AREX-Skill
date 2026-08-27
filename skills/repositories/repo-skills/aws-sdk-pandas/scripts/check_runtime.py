#!/usr/bin/env python3
"""Check awswrangler importability, installed extras, and visible config.

This helper is safe to run from any directory as long as awswrangler is
installed in the active Python environment.

Examples
--------
python scripts/check_runtime.py
python scripts/check_runtime.py --show-config
python scripts/check_runtime.py --check-common-extras
python scripts/check_runtime.py --require gremlin_python --require SPARQLWrapper
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections.abc import Iterable
from typing import Any

COMMON_EXTRAS: dict[str, tuple[str, str]] = {
    "redshift": ("redshift_connector", "awswrangler[redshift]"),
    "mysql": ("pymysql", "awswrangler[mysql]"),
    "postgres": ("pg8000", "awswrangler[postgres]"),
    "sqlserver": ("pyodbc", "awswrangler[sqlserver]"),
    "oracle": ("oracledb", "awswrangler[oracle]"),
    "opensearch": ("opensearchpy", "awswrangler[opensearch]"),
    "gremlin": ("gremlin_python", "awswrangler[gremlin]"),
    "sparql": ("SPARQLWrapper", "awswrangler[sparql]"),
    "openpyxl": ("openpyxl", "awswrangler[openpyxl]"),
    "deltalake": ("deltalake", "awswrangler[deltalake]"),
    "pyiceberg": ("pyiceberg", "awswrangler[pyiceberg]"),
    "modin": ("modin", "awswrangler[modin,ray]"),
    "ray": ("ray", "awswrangler[modin,ray]"),
}

SENSITIVE_NAME_FRAGMENTS = ("password", "secret", "token", "access_key", "session_token", "redis_password")


def _module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _redact_config_value(name: str, value: Any) -> Any:
    lowered = name.lower()
    if any(fragment in lowered for fragment in SENSITIVE_NAME_FRAGMENTS):
        return "<redacted>"
    if isinstance(value, (dict, list)):
        return value
    return value


def _unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Print the current wr.config table with sensitive values redacted.",
    )
    parser.add_argument(
        "--check-common-extras",
        action="store_true",
        help="Check the common optional dependency modules used by this repository.",
    )
    parser.add_argument(
        "--require",
        action="append",
        default=[],
        metavar="MODULE",
        help="Require a specific importable module name and return a non-zero exit code if it is missing.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a compact human summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        import awswrangler as wr
    except Exception as exc:  # pragma: no cover - import failure is the whole point
        print(f"ERROR: unable to import awswrangler: {exc}", file=sys.stderr)
        return 1

    report: dict[str, Any] = {
        "import_ok": True,
        "version": wr.__version__,
        "engine": str(wr.engine.get()),
        "memory_format": str(wr.memory_format.get()),
        "required_modules": [],
        "optional_modules": [],
    }

    missing_required: list[str] = []
    for module_name in _unique(args.require):
        available = _module_available(module_name)
        report["required_modules"].append({"module": module_name, "available": available})
        if not available:
            missing_required.append(module_name)

    if args.check_common_extras:
        for extra_name, (module_name, install_hint) in COMMON_EXTRAS.items():
            available = _module_available(module_name)
            report["optional_modules"].append(
                {
                    "extra": extra_name,
                    "module": module_name,
                    "available": available,
                    "install_hint": install_hint,
                }
            )

    if args.show_config:
        config_rows = []
        for row in wr.config.to_pandas().to_dict(orient="records"):
            config_rows.append(
                {
                    "name": row.get("name"),
                    "configured": row.get("configured"),
                    "parent_parameter_name": row.get("parent_parameter_name"),
                    "value": _redact_config_value(str(row.get("name", "")), row.get("value")),
                }
            )
        report["config"] = config_rows

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(f"awswrangler {report['version']}")
        print(f"engine={report['engine']} memory_format={report['memory_format']}")
        if args.require:
            for item in report["required_modules"]:
                status = "ok" if item["available"] else "missing"
                print(f"require {item['module']}: {status}")
        if args.check_common_extras:
            for item in report["optional_modules"]:
                status = "ok" if item["available"] else f"missing -> pip install {item['install_hint']}"
                print(f"extra {item['extra']} ({item['module']}): {status}")
        if args.show_config:
            print("config:")
            for item in report["config"]:
                value = item["value"]
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, sort_keys=True, default=str)
                print(f"  {item['name']}: configured={item['configured']} value={value}")

    return 1 if missing_required else 0


if __name__ == "__main__":
    raise SystemExit(main())
