#!/usr/bin/env python3
"""Inspect public torchtune model-family builders without instantiating models."""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass

DEFAULT_FAMILIES = [
    "llama4",
    "llama3_3",
    "llama3_2",
    "llama3_2_vision",
    "llama3",
    "llama3_1",
    "llama2",
    "qwen2",
    "qwen2_5",
    "qwen3",
    "gemma",
    "gemma2",
    "mistral",
    "phi3",
    "phi4",
    "clip",
    "flux",
    "t5",
    "smol",
]


@dataclass
class ExportInfo:
    family: str
    name: str
    dotpath: str
    kind: str
    signature: str | None
    error: str | None = None


@dataclass
class FamilyResult:
    family: str
    module: str
    ok: bool
    exports: list[ExportInfo]
    error: str | None = None


def _kind(value: object) -> str:
    if inspect.isclass(value):
        return "class"
    if inspect.isfunction(value):
        return "function"
    if callable(value):
        return "callable"
    return type(value).__name__


def _signature(value: object) -> tuple[str | None, str | None]:
    if not callable(value):
        return None, None
    try:
        return str(inspect.signature(value)), None
    except Exception as exc:  # pragma: no cover - depends on optional deps/proxies
        return None, f"{type(exc).__name__}: {exc}"


def inspect_family(family: str) -> FamilyResult:
    module_name = f"torchtune.models.{family}"
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        return FamilyResult(
            family=family,
            module=module_name,
            ok=False,
            exports=[],
            error=f"{type(exc).__name__}: {exc}",
        )

    names = list(getattr(module, "__all__", []))
    if not names:
        names = [name for name in dir(module) if not name.startswith("_")]

    exports: list[ExportInfo] = []
    for name in names:
        try:
            value = getattr(module, name)
        except Exception as exc:  # pragma: no cover - defensive only
            exports.append(
                ExportInfo(
                    family=family,
                    name=name,
                    dotpath=f"{module_name}.{name}",
                    kind="unavailable",
                    signature=None,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
            continue
        signature, error = _signature(value)
        exports.append(
            ExportInfo(
                family=family,
                name=name,
                dotpath=f"{module_name}.{name}",
                kind=_kind(value),
                signature=signature,
                error=error,
            )
        )
    return FamilyResult(family=family, module=module_name, ok=True, exports=exports)


def _print_table(results: Iterable[FamilyResult], include_non_callables: bool) -> None:
    for result in results:
        print(f"# {result.module}")
        if not result.ok:
            print(f"IMPORT FAILED: {result.error}\n")
            continue
        rows = result.exports
        if not include_non_callables:
            rows = [row for row in rows if row.kind in {"function", "class", "callable"}]
        if not rows:
            print("(no matching public exports)\n")
            continue
        for row in rows:
            signature = row.signature or ""
            suffix = f"  [{row.error}]" if row.error else ""
            print(f"{row.dotpath}{signature}  ({row.kind}){suffix}")
        print()


def _jsonable(results: Iterable[FamilyResult], include_non_callables: bool) -> list[dict[str, object]]:
    output = []
    for result in results:
        data = asdict(result)
        if not include_non_callables:
            data["exports"] = [
                asdict(row)
                for row in result.exports
                if row.kind in {"function", "class", "callable"}
            ]
        output.append(data)
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "List callable public exports from torchtune.models family modules. "
            "The script imports modules but never instantiates model builders."
        )
    )
    parser.add_argument(
        "--families",
        nargs="+",
        default=DEFAULT_FAMILIES,
        help="Model family module names under torchtune.models, e.g. llama3 qwen2_5.",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format.",
    )
    parser.add_argument(
        "--include-non-callables",
        action="store_true",
        help="Include public exports that are not callable.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = [inspect_family(family) for family in args.families]
    if args.format == "json":
        print(json.dumps(_jsonable(results, args.include_non_callables), indent=2, sort_keys=True))
    else:
        _print_table(results, args.include_non_callables)
    return 0 if all(result.ok for result in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
