#!/usr/bin/env python3
"""Inspect safetensors header metadata without loading tensor payloads.

This helper is intentionally read-only. It opens a safetensors file, prints
metadata as JSON, and can optionally include a compact tensor-key summary for
planning model utility work.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _import_safe_open():
    try:
        from safetensors import safe_open
    except ImportError as exc:
        raise SystemExit(
            "safetensors is required. Install it in the active Python environment "
            "before inspecting .safetensors metadata."
        ) from exc
    return safe_open


def _json_default(value: Any) -> str:
    return str(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read safetensors metadata without loading model tensors."
    )
    parser.add_argument("model", help="Path to a .safetensors model, LoRA, or adapter file.")
    parser.add_argument(
        "--include-keys",
        action="store_true",
        help="Also print tensor key count and a bounded sample of tensor keys.",
    )
    parser.add_argument(
        "--max-keys",
        type=int,
        default=25,
        help="Maximum tensor keys to include when --include-keys is set.",
    )
    parser.add_argument(
        "--require-metadata",
        action="store_true",
        help="Exit non-zero if the file has no metadata entries.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    model_path = Path(args.model)

    if model_path.suffix != ".safetensors":
        print(f"error: expected a .safetensors file, got: {model_path}", file=sys.stderr)
        return 2
    if not model_path.is_file():
        print(f"error: file not found: {model_path}", file=sys.stderr)
        return 2
    if args.max_keys < 0:
        print("error: --max-keys must be non-negative", file=sys.stderr)
        return 2

    safe_open = _import_safe_open()

    try:
        with safe_open(str(model_path), framework="pt", device="cpu") as handle:
            metadata = handle.metadata() or {}
            result: dict[str, Any] = {
                "path": str(model_path),
                "metadata": metadata,
                "metadata_key_count": len(metadata),
            }
            if args.include_keys:
                keys = list(handle.keys())
                result["tensor_key_count"] = len(keys)
                result["tensor_keys_sample"] = keys[: args.max_keys]
    except Exception as exc:  # safetensors raises several parse/header errors.
        print(f"error: failed to read safetensors header: {exc}", file=sys.stderr)
        return 1

    if args.require_metadata and not metadata:
        print(json.dumps(result, indent=2, sort_keys=True, default=_json_default))
        print("error: no metadata entries found", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, sort_keys=True, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
