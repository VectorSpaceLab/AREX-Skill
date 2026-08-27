#!/usr/bin/env python3
"""Offline setup checker for Chinese-BERT-wwm family workflows.

This helper verifies that the active Python environment has the minimum public
libraries needed for the Transformers loading path and prints the bundled HFL
model-id map. It never downloads checkpoints, opens network sockets, trains
models, or mutates caches.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib import metadata
from typing import Any

MODEL_IDS = {
    "hfl/chinese-bert-wwm": "BERT-wwm",
    "hfl/chinese-bert-wwm-ext": "BERT-wwm-ext",
    "hfl/chinese-roberta-wwm-ext": "RoBERTa-wwm-ext",
    "hfl/chinese-roberta-wwm-ext-large": "RoBERTa-wwm-ext-large",
    "hfl/rbt3": "RBT3",
    "hfl/rbt4": "RBT4",
    "hfl/rbt6": "RBT6",
    "hfl/rbtl3": "RBTL3",
}

REQUIRED_TRANSFORMERS_ATTRS = [
    "BertTokenizer",
    "BertModel",
    "AutoTokenizer",
    "AutoModel",
    "BertConfig",
]


def version_or_none(distribution: str) -> str | None:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def import_module(name: str) -> tuple[Any | None, str | None]:
    try:
        return importlib.import_module(name), None
    except Exception as exc:  # pragma: no cover - environment dependent
        return None, f"{type(exc).__name__}: {exc}"


def check_transformers() -> dict[str, Any]:
    module, error = import_module("transformers")
    result: dict[str, Any] = {
        "installed": module is not None,
        "version": version_or_none("transformers"),
        "import_error": error,
        "required_attrs": {},
    }
    if module is None:
        return result
    for attr in REQUIRED_TRANSFORMERS_ATTRS:
        try:
            getattr(module, attr)
            result["required_attrs"][attr] = "ok"
        except Exception as exc:  # lazy imports can raise backend errors
            result["required_attrs"][attr] = f"error: {type(exc).__name__}: {exc}"
    return result


def check_torch() -> dict[str, Any]:
    module, error = import_module("torch")
    result: dict[str, Any] = {
        "installed": module is not None,
        "version": version_or_none("torch"),
        "import_error": error,
        "cuda_available": None,
        "cuda_version": None,
    }
    if module is None:
        return result
    try:
        result["cuda_available"] = bool(module.cuda.is_available())
    except Exception as exc:  # pragma: no cover - backend dependent
        result["cuda_available"] = f"error: {type(exc).__name__}: {exc}"
    result["cuda_version"] = getattr(getattr(module, "version", None), "cuda", None)
    return result


def build_report() -> dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "model_ids": MODEL_IDS,
        "class_policy": "Use BertTokenizer/BertModel or AutoTokenizer/AutoModel; do not use RobertaTokenizer/RobertaModel for the listed RoBERTa-wwm names.",
        "transformers": check_transformers(),
        "torch": check_torch(),
        "paddlehub": {
            "installed": importlib.util.find_spec("paddlehub") is not None if hasattr(importlib, "util") else None,
            "version": version_or_none("paddlehub"),
            "note": "PaddleHub is optional; absence does not block Transformers workflows.",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check local Python support for Chinese-BERT-wwm Transformers workflows without downloads."
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--require-transformers", action="store_true", help="Return nonzero if Transformers or required BERT/Auto classes are unavailable.")
    parser.add_argument("--list-models", action="store_true", help="Print the bundled HFL model-id map and exit.")
    args = parser.parse_args(argv)

    if args.list_models:
        for model_id, display in MODEL_IDS.items():
            print(f"{model_id}\t{display}")
        return 0

    report = build_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        print(f"Transformers: {report['transformers']['version'] or 'not installed'}")
        print(f"Torch: {report['torch']['version'] or 'not installed'}")
        print(f"Torch CUDA available: {report['torch']['cuda_available']}")
        print("Supported HFL model ids:")
        for model_id, display in MODEL_IDS.items():
            print(f"- {model_id}: {display}")
        print(report["class_policy"])

    if args.require_transformers:
        transformers = report["transformers"]
        if not transformers["installed"]:
            print("Transformers is not installed in this Python environment.", file=sys.stderr)
            return 1
        failed = {k: v for k, v in transformers["required_attrs"].items() if v != "ok"}
        if failed:
            print(f"Transformers required class import failed: {failed}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
