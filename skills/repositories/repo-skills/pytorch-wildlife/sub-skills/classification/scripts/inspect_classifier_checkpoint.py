#!/usr/bin/env python3
"""Safely inspect a local PytorchWildlife classifier checkpoint.

This helper only reads a checkpoint with PyTorch's restricted weights-only
loader. It never constructs a model, downloads weights, writes files, or
executes inference.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def _shape(value: Any) -> list[int] | None:
    shape = getattr(value, "shape", None)
    if shape is None:
        return None
    try:
        return [int(dim) for dim in shape]
    except (TypeError, ValueError):
        return None


def _load(path: Path) -> Any:
    import torch

    # Deliberately do not fall back to the unrestricted pickle loader.
    return torch.load(path, map_location="cpu", weights_only=True)


def inspect_checkpoint(path: Path) -> dict[str, Any]:
    checkpoint = _load(path)
    report: dict[str, Any] = {
        "path": str(path),
        "checkpoint_type": type(checkpoint).__name__,
    }
    if not isinstance(checkpoint, dict):
        report["error"] = "checkpoint is not a mapping"
        return report

    report["top_level_keys"] = [str(key) for key in checkpoint.keys()]
    state_key = next(
        (key for key in ("state_dict", "model_state_dict") if key in checkpoint),
        None,
    )
    report["state_key"] = state_key
    if state_key is None or not isinstance(checkpoint[state_key], dict):
        report["error"] = "no mapping under state_dict or model_state_dict"
        return report

    state = checkpoint[state_key]
    keys = [str(key) for key in state.keys()]
    report["state_key_count"] = len(keys)
    prefixes = Counter(key.split(".", 1)[0] for key in keys if "." in key)
    report["leading_key_prefixes"] = dict(prefixes.most_common(12))

    interesting: dict[str, list[int]] = {}
    for key, value in state.items():
        key_text = str(key)
        if key_text.endswith((
            "classifier.weight",
            "classifier.bias",
            "head.weight",
            "head.bias",
            "head.fc.weight",
            "head.fc.bias",
            "fc.weight",
            "fc.bias",
        )):
            shape = _shape(value)
            if shape is not None:
                interesting[key_text] = shape
    report["classifier_like_tensors"] = interesting
    output_rows = sorted(
        {shape[0] for key, shape in interesting.items() if key.endswith("weight") and shape}
    )
    report["candidate_output_dimensions"] = output_rows
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect classifier checkpoint keys and output dimensions without model construction."
    )
    parser.add_argument("checkpoint", type=Path, help="local checkpoint file")
    parser.add_argument(
        "--json", action="store_true", dest="as_json", help="emit machine-readable JSON"
    )
    args = parser.parse_args(argv)
    path = args.checkpoint.expanduser()
    if not path.is_file():
        parser.error(f"checkpoint is not a readable file: {path}")
    try:
        report = inspect_checkpoint(path)
    except Exception as exc:  # report a concise, non-traceback diagnostic
        report = {
            "path": str(path),
            "error": f"restricted checkpoint read failed: {type(exc).__name__}: {exc}",
        }
        if args.as_json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(report["error"], file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")
    return 0 if "error" not in report else 1


if __name__ == "__main__":
    raise SystemExit(main())
