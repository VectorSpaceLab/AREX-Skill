#!/usr/bin/env python3
"""Inspect ColBERT checkpoint configuration without forcing full model encoding."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


def _is_probably_local_checkpoint(value: str) -> bool:
    return value.endswith(".dnn") or os.path.exists(value)


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return str(value)


def _config_to_dict(config: Any) -> dict[str, Any] | None:
    if config is None:
        return None
    if is_dataclass(config):
        data = asdict(config)
    elif hasattr(config, "export"):
        data = config.export()
    else:
        data = dict(getattr(config, "__dict__", {}))
    return {
        str(key): _jsonable(value)
        for key, value in data.items()
        if not str(key).startswith("_")
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Load and summarize ColBERTConfig metadata for a checkpoint. "
            "Prefer local paths; remote names require --allow-remote."
        )
    )
    parser.add_argument(
        "--checkpoint",
        required=True,
        help="Local ColBERT checkpoint directory/.dnn file, or a Hugging Face name with --allow-remote.",
    )
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        help="Allow non-local Hugging Face model/repo names that may require network or cache access.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full loaded config as JSON instead of a concise summary.",
    )
    args = parser.parse_args()

    if not args.allow_remote and not _is_probably_local_checkpoint(args.checkpoint):
        print(
            "Refusing non-local checkpoint name without --allow-remote. "
            "Pass a local checkpoint path for offline-safe inspection.",
            file=sys.stderr,
        )
        return 2

    try:
        from colbert.infra import ColBERTConfig
    except Exception as exc:  # pragma: no cover - diagnostic script
        print(f"Failed to import ColBERTConfig: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    try:
        config = ColBERTConfig.load_from_checkpoint(args.checkpoint)
    except Exception as exc:  # pragma: no cover - depends on local package/checkpoint
        print(f"Failed to load checkpoint config: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if config is None:
        print("No ColBERT artifact metadata was found for this checkpoint.")
        print(
            "If this is a generic Hugging Face backbone, pass an explicit "
            "ColBERTConfig when constructing a tokenizer or model."
        )
        return 3

    data = _config_to_dict(config) or {}
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return 0

    fields = [
        "checkpoint",
        "model_name",
        "dim",
        "query_maxlen",
        "doc_maxlen",
        "query_token",
        "query_token_id",
        "doc_token",
        "doc_token_id",
        "attend_to_mask_tokens",
        "mask_punctuation",
        "similarity",
        "interaction",
        "amp",
        "gpus",
        "nbits",
        "load_index_with_mmap",
    ]

    print("ColBERT checkpoint config summary")
    for field in fields:
        print(f"{field}: {data.get(field)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
