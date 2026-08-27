#!/usr/bin/env python3
"""Validate ComfyUI-LTXVideo conditioning safetensors artifacts.

This helper inspects tensor keys, shapes, dtypes, and metadata only. It does not
import ComfyUI, load models, download files, call APIs, or run generation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

DATA_RE = re.compile(r"^conditioning_data_(\d+)$")
MASK_RE = re.compile(r"^attention_mask_(\d+)$")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate that a safetensors file has ComfyUI-LTXVideo "
            "conditioning_data_* tensors and optional matching attention_mask_* tensors."
        )
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Path to a conditioning .safetensors file produced by LTXVSaveConditioning.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Treat unknown tensor keys, orphan attention masks, non-contiguous numeric "
            "indices, and shape warnings as validation errors."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable JSON report instead of a text summary.",
    )
    return parser


def tensor_info(tensor: Any) -> dict[str, Any]:
    shape = list(getattr(tensor, "shape", []))
    dtype = str(getattr(tensor, "dtype", "unknown"))
    numel_attr = getattr(tensor, "numel", None)
    if callable(numel_attr):
        numel = int(numel_attr())
    else:
        size = 1
        for dim in shape:
            size *= int(dim)
        numel = size if shape else 0
    return {"shape": shape, "dtype": dtype, "numel": numel}


def validate(path: Path, strict: bool = False) -> tuple[int, dict[str, Any]]:
    report: dict[str, Any] = {
        "path": str(path),
        "ok": False,
        "metadata": {},
        "conditioning": [],
        "attention_masks": [],
        "warnings": [],
        "errors": [],
    }

    if not path.exists():
        report["errors"].append(f"File does not exist: {path}")
        return 1, report
    if not path.is_file():
        report["errors"].append(f"Path is not a file: {path}")
        return 1, report
    if path.suffix != ".safetensors":
        report["warnings"].append(
            f"File suffix is {path.suffix!r}; expected '.safetensors'."
        )

    try:
        from safetensors import safe_open
    except Exception as exc:  # pragma: no cover - environment dependent
        report["errors"].append(
            "Python package 'safetensors' is required to inspect this file: "
            f"{exc}"
        )
        return 1, report

    try:
        with safe_open(str(path), framework="pt", device="cpu") as handle:
            keys = sorted(handle.keys())
            report["metadata"] = dict(handle.metadata() or {})

            data_indices: dict[int, str] = {}
            mask_indices: dict[int, str] = {}
            unknown_keys: list[str] = []
            malformed_keys: list[str] = []

            for key in keys:
                data_match = DATA_RE.match(key)
                mask_match = MASK_RE.match(key)
                if data_match:
                    data_indices[int(data_match.group(1))] = key
                elif mask_match:
                    mask_indices[int(mask_match.group(1))] = key
                elif key.startswith("conditioning_data_") or key.startswith(
                    "attention_mask_"
                ):
                    malformed_keys.append(key)
                else:
                    unknown_keys.append(key)

            if not data_indices:
                report["errors"].append("No conditioning_data_* tensors found.")

            for key in malformed_keys:
                report["errors"].append(
                    f"Malformed conditioning tensor key {key!r}; suffix must be numeric."
                )

            if unknown_keys:
                message = f"Unknown tensor key(s): {', '.join(unknown_keys)}"
                if strict:
                    report["errors"].append(message)
                else:
                    report["warnings"].append(message)

            if data_indices:
                sorted_indices = sorted(data_indices)
                expected = list(range(sorted_indices[0], sorted_indices[-1] + 1))
                if sorted_indices != expected:
                    message = (
                        "conditioning_data_* indices are non-contiguous: "
                        f"found {sorted_indices}, expected {expected}."
                    )
                    if strict:
                        report["errors"].append(message)
                    else:
                        report["warnings"].append(message)

            for idx in sorted(data_indices):
                key = data_indices[idx]
                tensor = handle.get_tensor(key)
                info = tensor_info(tensor)
                entry = {"index": idx, "key": key, **info}
                report["conditioning"].append(entry)
                if info["numel"] == 0:
                    report["errors"].append(f"{key} is empty.")
                if len(info["shape"]) < 2:
                    message = f"{key} has rank {len(info['shape'])}; expected a sequence-like tensor."
                    if strict:
                        report["errors"].append(message)
                    else:
                        report["warnings"].append(message)

            for idx in sorted(mask_indices):
                key = mask_indices[idx]
                tensor = handle.get_tensor(key)
                info = tensor_info(tensor)
                entry = {"index": idx, "key": key, **info}
                report["attention_masks"].append(entry)
                if idx not in data_indices:
                    message = f"{key} has no matching conditioning_data_{idx}."
                    if strict:
                        report["errors"].append(message)
                    else:
                        report["warnings"].append(message)
                if info["numel"] == 0:
                    report["errors"].append(f"{key} is empty.")

            data_info = {item["index"]: item for item in report["conditioning"]}
            for mask in report["attention_masks"]:
                data = data_info.get(mask["index"])
                if data is None:
                    continue
                data_shape = data["shape"]
                mask_shape = mask["shape"]
                if data_shape and mask_shape and data_shape[0] != mask_shape[0]:
                    message = (
                        f"{mask['key']} batch dimension {mask_shape[0]} does not "
                        f"match {data['key']} batch dimension {data_shape[0]}."
                    )
                    if strict:
                        report["errors"].append(message)
                    else:
                        report["warnings"].append(message)
                if len(data_shape) >= 2 and len(mask_shape) >= 2:
                    if data_shape[1] != mask_shape[-1]:
                        message = (
                            f"{mask['key']} token dimension {mask_shape[-1]} does not "
                            f"match {data['key']} token dimension {data_shape[1]}."
                        )
                        if strict:
                            report["errors"].append(message)
                        else:
                            report["warnings"].append(message)

    except Exception as exc:  # pragma: no cover - depends on file corruption details
        report["errors"].append(f"Failed to read safetensors file: {exc}")
        return 1, report

    report["ok"] = not report["errors"]
    return (0 if report["ok"] else 1), report


def print_text(report: dict[str, Any]) -> None:
    status = "OK" if report["ok"] else "FAILED"
    print(f"{status}: {report['path']}")
    if report["metadata"]:
        print("metadata:")
        for key, value in sorted(report["metadata"].items()):
            print(f"  {key}: {value}")
    print(f"conditioning tensors: {len(report['conditioning'])}")
    for item in report["conditioning"]:
        print(
            f"  {item['key']}: shape={item['shape']} dtype={item['dtype']} "
            f"numel={item['numel']}"
        )
    print(f"attention masks: {len(report['attention_masks'])}")
    for item in report["attention_masks"]:
        print(
            f"  {item['key']}: shape={item['shape']} dtype={item['dtype']} "
            f"numel={item['numel']}"
        )
    if report["warnings"]:
        print("warnings:")
        for message in report["warnings"]:
            print(f"  - {message}")
    if report["errors"]:
        print("errors:")
        for message in report["errors"]:
            print(f"  - {message}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    exit_code, report = validate(args.path, strict=args.strict)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
