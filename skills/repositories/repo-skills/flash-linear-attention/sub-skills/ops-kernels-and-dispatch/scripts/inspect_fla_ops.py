#!/usr/bin/env python3
"""Safely inspect public fla.ops exports without executing kernels."""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import sys
from collections.abc import Iterable
from typing import Any


KNOWN_SMOKE_OPS = ("chunk_gla", "chunk_linear_attn", "chunk_kda")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import fla.ops, list public operator exports, and optionally print signatures. No kernels are executed.",
    )
    parser.add_argument(
        "--filter",
        metavar="TEXT",
        help="Only list public op names containing TEXT (case-insensitive).",
    )
    parser.add_argument(
        "--signature",
        metavar="NAME",
        action="append",
        default=[],
        help="Print inspect.signature for a public op. May be repeated.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human-readable text.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Check that representative public ops are exported and print a tiny import summary.",
    )
    return parser.parse_args(argv)


def import_ops_module() -> Any:
    # When the helper is run from a source checkout, Python places this script's
    # directory on sys.path rather than the repository root. Add the current
    # working directory first so an editable checkout works without hard-coded
    # paths. Installed packages still import normally when no local checkout is
    # present.
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)
    try:
        return importlib.import_module("fla.ops")
    except Exception as exc:  # pragma: no cover - depends on user environment
        raise SystemExit(f"ERROR: failed to import fla.ops: {exc.__class__.__name__}: {exc}") from exc


def public_ops(ops_module: Any) -> list[str]:
    exported = getattr(ops_module, "__all__", None)
    if exported is None:
        exported = [name for name in dir(ops_module) if not name.startswith("_")]
    return sorted(str(name) for name in exported)


def filter_ops(names: Iterable[str], text: str | None) -> list[str]:
    if not text:
        return list(names)
    needle = text.casefold()
    return [name for name in names if needle in name.casefold()]


def signature_for(ops_module: Any, name: str) -> str:
    if name not in public_ops(ops_module):
        raise KeyError(f"{name!r} is not listed in fla.ops.__all__")
    obj = getattr(ops_module, name, None)
    if obj is None:
        raise AttributeError(f"fla.ops exports {name!r} but the attribute is missing")
    try:
        return f"{name}{inspect.signature(obj)}"
    except (TypeError, ValueError) as exc:
        return f"{name}<signature unavailable: {exc}>"


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    ops_module = import_ops_module()
    names = public_ops(ops_module)
    listed = filter_ops(names, args.filter)

    sigs: dict[str, str] = {}
    errors: dict[str, str] = {}
    for name in args.signature:
        try:
            sigs[name] = signature_for(ops_module, name)
        except Exception as exc:  # pragma: no cover - user input dependent
            errors[name] = f"{exc.__class__.__name__}: {exc}"

    smoke_missing = [name for name in KNOWN_SMOKE_OPS if name not in names]
    return {
        "module": "fla.ops",
        "export_count": len(names),
        "listed_count": len(listed),
        "filter": args.filter,
        "ops": listed,
        "signatures": sigs,
        "errors": errors,
        "smoke": {
            "requested": bool(args.smoke),
            "known_ops": list(KNOWN_SMOKE_OPS),
            "missing": smoke_missing,
            "ok": not smoke_missing,
        },
    }


def print_human(payload: dict[str, Any], args: argparse.Namespace) -> None:
    if args.smoke:
        smoke = payload["smoke"]
        status = "ok" if smoke["ok"] else "missing: " + ", ".join(smoke["missing"])
        print(f"smoke: {status}")
    print(f"module: {payload['module']}")
    print(f"public exports: {payload['export_count']}")
    if args.filter:
        print(f"filtered exports ({payload['listed_count']}, filter={args.filter!r}):")
    else:
        print(f"exports ({payload['listed_count']}):")
    for name in payload["ops"]:
        print(f"  {name}")
    if payload["signatures"]:
        print("signatures:")
        for name in args.signature:
            if name in payload["signatures"]:
                print(f"  {payload['signatures'][name]}")
    if payload["errors"]:
        print("errors:", file=sys.stderr)
        for name, error in payload["errors"].items():
            print(f"  {name}: {error}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload(args)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_human(payload, args)
    return 1 if payload["errors"] or (args.smoke and not payload["smoke"]["ok"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
