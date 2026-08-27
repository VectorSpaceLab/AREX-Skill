#!/usr/bin/env python3
"""Inspect installed scvi-tools core model APIs.

This script imports models from the active Python environment and prints
constructor, setup_anndata, and train signatures for selected core models.
It does not read the original scvi-tools source checkout.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from collections.abc import Iterable
from typing import Any

DEFAULT_MODELS = [
    "SCVI",
    "SCANVI",
    "TOTALVI",
    "PEAKVI",
    "MULTIVI",
    "AUTOZI",
    "LinearSCVI",
    "CondSCVI",
    "DestVI",
    "AmortizedLDA",
    "mlxSCVI",
]


def _load_scvi_model_module():
    try:
        return importlib.import_module("scvi.model")
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise SystemExit(f"Could not import scvi.model from this environment: {exc}") from exc


def _signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError) as exc:
        return f"<signature unavailable: {exc}>"


def inspect_model(name: str, model_module: Any) -> dict[str, Any]:
    if not hasattr(model_module, name):
        return {
            "model": name,
            "available": False,
            "error": f"scvi.model has no attribute {name!r}",
        }

    cls = getattr(model_module, name)
    setup = getattr(cls, "setup_anndata", None)
    train = getattr(cls, "train", None)
    return {
        "model": name,
        "available": True,
        "class": f"{cls.__module__}.{cls.__qualname__}",
        "init": _signature(cls),
        "setup_anndata": _signature(setup) if setup is not None else None,
        "train": _signature(train) if train is not None else None,
        "doc_summary": (inspect.getdoc(cls) or "").splitlines()[0:3],
    }


def print_text(results: Iterable[dict[str, Any]]) -> None:
    for item in results:
        print(f"## {item['model']}")
        if not item.get("available"):
            print(f"available: false")
            print(f"error: {item['error']}\n")
            continue
        print(f"class: {item['class']}")
        print(f"__init__: {item['init']}")
        print(f"setup_anndata: {item['setup_anndata']}")
        print(f"train: {item['train']}")
        if item.get("doc_summary"):
            print("doc: " + " ".join(item["doc_summary"]))
        print()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect installed scvi-tools core model signatures.",
    )
    parser.add_argument(
        "--model",
        action="append",
        choices=DEFAULT_MODELS,
        help="Model to inspect. May be repeated. Defaults to all core models.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human-readable text.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    model_names = args.model or DEFAULT_MODELS
    model_module = _load_scvi_model_module()
    results = [inspect_model(name, model_module) for name in model_names]

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        print_text(results)

    return 0 if all(item.get("available") for item in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
