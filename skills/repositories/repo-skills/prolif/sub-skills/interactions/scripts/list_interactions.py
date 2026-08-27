#!/usr/bin/env python3
"""Inspect ProLIF interaction names and constructor signatures safely."""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class InteractionInfo:
    name: str
    category: str
    signature: str | None = None
    doc: str | None = None
    error: str | None = None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "List ProLIF interactions and optionally show constructor signatures "
            "and doc snippets. This helper does not read or write molecular data."
        )
    )
    parser.add_argument(
        "names",
        nargs="*",
        help="Optional interaction names to inspect when --details is used.",
    )
    parser.add_argument(
        "--include-bridged",
        action="store_true",
        help="Include bridged interactions such as WaterBridge.",
    )
    parser.add_argument(
        "--show-hidden",
        action="store_true",
        help="Include hidden base interaction classes exposed by ProLIF.",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="Show constructor signatures and short doc snippets.",
    )
    parser.add_argument(
        "--doc-lines",
        type=int,
        default=6,
        help="Maximum non-empty docstring lines per detailed interaction.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    return parser


def _import_prolif() -> tuple[Any, Any, Any]:
    try:
        fingerprint_module = importlib.import_module("prolif.fingerprint")
        base_module = importlib.import_module("prolif.interactions.base")
    except Exception as exc:  # pragma: no cover - depends on user's environment
        raise SystemExit(
            "Could not import ProLIF interaction modules. Install ProLIF with its "
            f"runtime dependencies, then retry. Import error: {exc}"
        ) from exc
    return (
        fingerprint_module.Fingerprint,
        base_module._BASE_INTERACTIONS,
        base_module._BRIDGED_INTERACTIONS,
    )


def _doc_snippet(obj: Any, max_lines: int) -> str:
    doc = inspect.getdoc(obj) or ""
    lines = [line.strip() for line in doc.splitlines() if line.strip()]
    return "\n".join(lines[: max(0, max_lines)])


def _category(name: str, hidden: set[str], bridged: set[str]) -> str:
    if name in bridged:
        return "bridged"
    if name in hidden:
        return "hidden"
    return "regular"


def _collect(args: argparse.Namespace) -> list[InteractionInfo]:
    Fingerprint, hidden_registry, bridged_registry = _import_prolif()
    hidden_names = set(hidden_registry)
    bridged_names = set(bridged_registry)
    available = Fingerprint.list_available(
        show_hidden=args.show_hidden,
        show_bridged=args.include_bridged,
    )
    selected = args.names if args.names else available
    known = set(available)
    if args.names:
        known.update(Fingerprint.list_available(show_hidden=True, show_bridged=True))

    infos: list[InteractionInfo] = []
    for name in selected:
        if name not in known:
            infos.append(
                InteractionInfo(
                    name=name,
                    category="unknown",
                    error="Unknown interaction name in this ProLIF environment.",
                )
            )
            continue
        if name not in available and name in bridged_names and not args.include_bridged:
            infos.append(
                InteractionInfo(
                    name=name,
                    category="bridged",
                    error="Use --include-bridged to include bridged interactions.",
                )
            )
            continue
        if name not in available and name in hidden_names and not args.show_hidden:
            infos.append(
                InteractionInfo(
                    name=name,
                    category="hidden",
                    error="Use --show-hidden to include base interaction classes.",
                )
            )
            continue

        cls = None
        category = _category(name, hidden_names, bridged_names)
        if category == "bridged":
            cls = bridged_registry.get(name)
        elif category == "hidden":
            cls = hidden_registry.get(name)
        else:
            interactions_module = importlib.import_module("prolif.interactions.base")
            cls = interactions_module._INTERACTIONS.get(name)

        info = InteractionInfo(name=name, category=category)
        if args.details:
            if cls is None:
                info.error = "Registered name could not be resolved to a class."
            else:
                try:
                    info.signature = str(inspect.signature(cls))
                except (TypeError, ValueError) as exc:
                    info.error = f"Could not inspect signature: {exc}"
                info.doc = _doc_snippet(cls, args.doc_lines)
        infos.append(info)
    return infos


def _print_text(infos: list[InteractionInfo], details: bool) -> None:
    if not details:
        for info in infos:
            suffix = f" [{info.category}]" if info.category != "regular" else ""
            if info.error:
                suffix += f" - {info.error}"
            print(f"{info.name}{suffix}")
        return

    for index, info in enumerate(infos):
        if index:
            print()
        print(f"{info.name} ({info.category})")
        if info.signature:
            print(f"  signature: {info.signature}")
        if info.doc:
            for line in info.doc.splitlines():
                print(f"  {line}")
        if info.error:
            print(f"  error: {info.error}")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    infos = _collect(args)
    if args.format == "json":
        print(json.dumps([asdict(info) for info in infos], indent=2, sort_keys=True))
    else:
        _print_text(infos, args.details)
    return 1 if any(info.category == "unknown" for info in infos) else 0


if __name__ == "__main__":
    raise SystemExit(main())
