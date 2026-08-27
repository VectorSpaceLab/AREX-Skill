#!/usr/bin/env python3
"""
Safely list public PyTorch Geometric Temporal dataset loader signatures.

This helper imports loader classes from torch_geometric_temporal.dataset but never
instantiates them, so it does not intentionally trigger dataset downloads or
cache writes. It is designed for planning before using web-backed loaders.

Examples:
  python scripts/list_dataset_loaders.py --format text
  python scripts/list_dataset_loaders.py --format json --include-index
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import sys
from typing import Any, Dict, Iterable, List, Optional


RAW_DATA_PLACEHOLDER = "<cwd>/data"


def _format_annotation(annotation: Any) -> Optional[str]:
    if annotation is inspect.Signature.empty:
        return None
    if isinstance(annotation, str):
        return annotation
    module = getattr(annotation, "__module__", None)
    qualname = getattr(annotation, "__qualname__", None)
    if module and qualname:
        if module == "builtins":
            return qualname
        return f"{module}.{qualname}"
    text = str(annotation)
    text = text.replace(os.getcwd(), "<cwd>")
    return text


def _safe_default(name: str, value: Any) -> str:
    if isinstance(value, str):
        normalized = value.replace(os.getcwd(), "<cwd>")
        if name == "raw_data_dir" and normalized.endswith("/data"):
            normalized = RAW_DATA_PLACEHOLDER
        return repr(normalized)
    return repr(value)


def _safe_signature(callable_obj: Any, *, drop_self: bool = True) -> str:
    try:
        sig = inspect.signature(callable_obj)
    except (TypeError, ValueError) as exc:
        return f"<unavailable: {exc}>"

    rendered: List[str] = []
    for name, param in sig.parameters.items():
        if drop_self and name == "self":
            continue
        piece = name
        if param.kind is inspect.Parameter.VAR_POSITIONAL:
            piece = "*" + piece
        elif param.kind is inspect.Parameter.VAR_KEYWORD:
            piece = "**" + piece

        annotation = _format_annotation(param.annotation)
        if annotation:
            piece += f": {annotation}"
        if param.default is not inspect.Signature.empty:
            piece += f" = {_safe_default(name, param.default)}"
        rendered.append(piece)

    return_annotation = _format_annotation(sig.return_annotation)
    suffix = f" -> {return_annotation}" if return_annotation else ""
    return "(" + ", ".join(rendered) + ")" + suffix


def _load_dataset_module():
    try:
        return importlib.import_module("torch_geometric_temporal.dataset")
    except Exception as exc:  # noqa: BLE001 - user-facing diagnostic helper
        print(
            "Failed to import torch_geometric_temporal.dataset. "
            "Install the package and any import-time dataset dependencies "
            "such as requests/tqdm before signature introspection.\n"
            f"Import error: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return None


def _iter_loader_classes(dataset_module: Any) -> Iterable[type]:
    for name in sorted(dir(dataset_module)):
        if not name.endswith("DatasetLoader"):
            continue
        obj = getattr(dataset_module, name)
        if inspect.isclass(obj):
            yield obj


def collect_loader_metadata(include_index: bool = False) -> List[Dict[str, Any]]:
    dataset_module = _load_dataset_module()
    if dataset_module is None:
        return []

    loaders: List[Dict[str, Any]] = []
    for cls in _iter_loader_classes(dataset_module):
        row: Dict[str, Any] = {
            "class": cls.__name__,
            "module": cls.__module__,
            "constructor": _safe_signature(cls.__init__),
            "methods": {},
        }
        for method_name in ("get_dataset", "get_index_dataset"):
            if method_name == "get_index_dataset" and not include_index:
                continue
            method = getattr(cls, method_name, None)
            if method is not None:
                row["methods"][method_name] = _safe_signature(method)
        loaders.append(row)
    return loaders


def emit_text(loaders: List[Dict[str, Any]], include_index: bool = False) -> None:
    if not loaders:
        print("No dataset loader classes found or dataset module could not be imported.")
        return
    print("PyTorch Geometric Temporal dataset loaders")
    print("(classes imported; no loader instances constructed)\n")
    for row in loaders:
        print(f"{row['class']}")
        print(f"  module: {row['module']}")
        print(f"  __init__{row['constructor']}")
        methods = row.get("methods", {})
        if "get_dataset" in methods:
            print(f"  get_dataset{methods['get_dataset']}")
        else:
            print("  get_dataset: <not present>")
        if include_index:
            if "get_index_dataset" in methods:
                print(f"  get_index_dataset{methods['get_index_dataset']}")
            else:
                print("  get_index_dataset: <not present>")
        print()


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "List torch_geometric_temporal.dataset loader signatures without "
            "instantiating loaders or downloading datasets."
        )
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Default: text.",
    )
    parser.add_argument(
        "--include-index",
        action="store_true",
        help="Also print get_index_dataset signatures when present.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    loaders = collect_loader_metadata(include_index=args.include_index)
    if args.format == "json":
        print(json.dumps({"loaders": loaders, "instantiated": False}, indent=2, sort_keys=True))
    else:
        emit_text(loaders, include_index=args.include_index)
    return 0 if loaders else 1


if __name__ == "__main__":
    raise SystemExit(main())
