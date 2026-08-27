#!/usr/bin/env python3
"""Check an active Python environment for DataChain runtime readiness.

The script is read-only: it imports DataChain, reports public package metadata,
probes selected optional namespaces, and can run a tiny local Query Engine smoke.
It does not read cloud storage, call Studio, invoke LLM providers, or mutate user
data.

Examples:
  python check_env.py
  python check_env.py --optional torch,hf --smoke
  python check_env.py --json
"""

import argparse
import importlib
import json
import os
from importlib import metadata
from typing import Any

OPTIONAL_IMPORTS = {
    "torch": "datachain.torch",
    "hf": "datachain.lib.hf",
    "video": "datachain.lib.video",
    "audio": "datachain.lib.audio",
    "zarr": "datachain.lib.zarr",
    "llm": "datachain.llm",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only DataChain environment check.")
    parser.add_argument(
        "--optional",
        default="torch,hf,video,audio,zarr,llm",
        help="Comma-separated optional probes to import (default: common optional surfaces).",
    )
    parser.add_argument("--smoke", action="store_true", help="Run a tiny local read_values/mutate smoke.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human report.")
    return parser


def import_status(module: str) -> dict[str, Any]:
    try:
        importlib.import_module(module)
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"module": module, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"module": module, "ok": True, "error": None}


def run_smoke() -> dict[str, Any]:
    os.environ.setdefault("DATACHAIN_NO_ANALYTICS", "1")
    import datachain as dc  # type: ignore

    with dc.Session(in_memory=True) as session:
        rows = (
            dc.read_values(x=[1, 2, 3], grp=["a", "a", "b"], session=session)
            .mutate(y=dc.C("x") + 1)
            .group_by(total=dc.func.sum("y"), partition_by="grp")
            .order_by("grp")
            .to_list("grp", "total")
        )
    expected = [("a", 5), ("b", 4)]
    if rows != expected:
        raise AssertionError(f"unexpected DataChain smoke rows: {rows!r}")
    if hasattr(dc.Session, "cleanup_for_tests"):
        dc.Session.cleanup_for_tests()
    return {"ok": True, "rows": rows}


def collect(optional: list[str], smoke: bool) -> dict[str, Any]:
    base = import_status("datachain")
    version = None
    if base["ok"]:
        try:
            version = metadata.version("datachain")
        except metadata.PackageNotFoundError:
            version = None
    optional_results = {
        name: import_status(OPTIONAL_IMPORTS[name])
        for name in optional
        if name in OPTIONAL_IMPORTS
    }
    return {
        "datachain_import": base,
        "distribution_version": version,
        "optional": optional_results,
        "smoke": run_smoke() if smoke and base["ok"] else None,
    }


def print_human(record: dict[str, Any]) -> None:
    base = record["datachain_import"]
    print(f"DataChain import: {'ok' if base['ok'] else 'failed'}")
    if not base["ok"]:
        print(f"  {base['error']}")
    print(f"Distribution version: {record['distribution_version'] or 'unknown'}")
    if record["optional"]:
        print("Optional probes:")
        for name, result in record["optional"].items():
            status = "ok" if result["ok"] else f"missing/failed ({result['error']})"
            print(f"  - {name}: {status}")
    if record.get("smoke"):
        print("Local smoke: ok")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    optional = [item.strip() for item in args.optional.split(",") if item.strip()]
    record = collect(optional, args.smoke)
    if args.json:
        print(json.dumps(record, indent=2))
    else:
        print_human(record)
    return 0 if record["datachain_import"]["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
