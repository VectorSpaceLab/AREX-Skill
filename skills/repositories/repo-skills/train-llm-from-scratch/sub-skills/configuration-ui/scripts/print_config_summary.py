#!/usr/bin/env python3
"""Summarize train-llm-from-scratch JSON configs without repo imports.

This helper reads ordinary JSON objects, prints their explicit keys and value
types, and optionally compares each config's explicit keys against a supplied
base JSON. It intentionally does not import the repository's config dataclasses
and never launches training.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

_MISSING = object()


def _warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as fh:
            obj = json.load(fh)
    except FileNotFoundError as exc:
        raise ValueError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"invalid JSON in {path}: line {exc.lineno} column {exc.colno}: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc

    if not isinstance(obj, dict):
        raise ValueError(f"expected top-level JSON object in {path}, got {type(obj).__name__}")
    return obj


def _flatten(obj: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in obj.items():
        dotted = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, Mapping):
            out.update(_flatten(value, dotted))
        else:
            out[dotted] = value
    return out


def _json_repr(value: Any) -> str:
    if value is _MISSING:
        return "<missing>"
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _print_summary(label: str, obj: dict[str, Any], base: dict[str, Any] | None) -> None:
    flat = _flatten(obj)
    print(f"## {label}")
    print(f"top-level explicit keys ({len(obj)}): {', '.join(sorted(obj)) if obj else '(none)'}")
    print(f"leaf explicit keys ({len(flat)}): {', '.join(sorted(flat)) if flat else '(none)'}")

    type_counts: dict[str, int] = {}
    for value in flat.values():
        tname = _type_name(value)
        type_counts[tname] = type_counts.get(tname, 0) + 1
    if type_counts:
        print("value types: " + ", ".join(f"{k}={v}" for k, v in sorted(type_counts.items())))

    null_keys = sorted(key for key, value in flat.items() if value is None)
    if null_keys:
        print("explicit null keys: " + ", ".join(null_keys))

    if base is not None:
        base_flat = _flatten(base)
        changed: list[tuple[str, Any, Any]] = []
        new: list[tuple[str, Any]] = []
        same: list[str] = []
        for key in sorted(flat):
            before = base_flat.get(key, _MISSING)
            if before is _MISSING:
                new.append((key, flat[key]))
            elif before == flat[key]:
                same.append(key)
            else:
                changed.append((key, before, flat[key]))

        print(f"compared to base: changed={len(changed)}, new={len(new)}, same_explicit={len(same)}")
        if changed:
            print("changed values:")
            for key, before, after in changed:
                print(f"  - {key}: {_json_repr(before)} -> {_json_repr(after)}")
        if new:
            print("keys absent from base:")
            for key, value in new:
                print(f"  - {key}: {_json_repr(value)}")
        if same:
            print("same-as-base explicit keys: " + ", ".join(same))
    print()


def _demo_objects() -> tuple[dict[str, Any], list[tuple[str, dict[str, Any]]]]:
    base = {
        "device": "cuda",
        "amp_dtype": "bf16",
        "context_length": 1024,
        "use_wandb": False,
        "log_dir": "/ephemeral/logs",
    }
    configs = [
        ("demo/smoke/base.json", {"device": "cpu", "amp_dtype": None, "context_length": 256}),
        ("demo/sft.json", {"batch_size": 8, "lr": 2e-5, "use_wandb": False}),
    ]
    return base, configs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize JSON config keys and explicit overrides without importing the repo.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("configs", nargs="*", type=Path, help="JSON config file(s) to summarize")
    parser.add_argument("--base", type=Path, help="optional base JSON to compare explicit keys against")
    parser.add_argument("--demo", action="store_true", help="run on a tiny in-memory fixture")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.demo:
        base, configs = _demo_objects()
        print("# Config summary demo")
        print("Fixture is in-memory; no files are read and no repository imports are used.\n")
        for label, obj in configs:
            _print_summary(label, obj, base)
        return 0

    if not args.configs:
        print("error: provide at least one config JSON or use --demo", file=sys.stderr)
        return 2

    ok = True
    base_obj: dict[str, Any] | None = None
    if args.base is not None:
        try:
            base_obj = _load_json_object(args.base)
            print(f"# Base: {args.base}\n")
        except ValueError as exc:
            _warn(str(exc))
            _warn("base comparison disabled")
            ok = False

    seen: set[Path] = set()
    for cfg_path in args.configs:
        normalized = cfg_path.resolve(strict=False)
        if normalized in seen:
            _warn(f"duplicate config path supplied: {cfg_path}")
        seen.add(normalized)
        try:
            obj = _load_json_object(cfg_path)
        except ValueError as exc:
            _warn(str(exc))
            ok = False
            continue
        _print_summary(str(cfg_path), obj, base_obj)

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
