#!/usr/bin/env python3
"""Validate xTuring finetuning inputs without launching training.

This helper checks a local dataset with the requested training mode and prints
an optional finetuning config summary for a named model key.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict


def load_finetuning_config(model_key: str) -> Dict[str, Any]:
    import xturing
    from xturing.config.read_config import read_yaml

    config_path = Path(xturing.__file__).resolve().parent / "config" / "finetuning_config.yaml"
    config = read_yaml(config_path)
    if model_key not in config:
        raise KeyError(f"Unknown model key: {model_key}")
    merged = dict(config["defaults"])
    merged.update(config[model_key])
    return merged


def summarize_dataset(kind: str, dataset_path: str) -> Dict[str, Any]:
    from xturing.datasets import InstructionDataset, PreferenceDataset, TextDataset

    dataset_classes = {
        "text": TextDataset,
        "instruction": InstructionDataset,
        "preference": PreferenceDataset,
    }
    dataset = dataset_classes[kind](dataset_path)
    train_split = dataset.data["train"]
    row_count = len(dataset)
    first_row = dataset[0] if row_count else {}
    return {
        "kind": kind,
        "rows": row_count,
        "columns": list(train_split.column_names),
        "sample_keys": list(first_row.keys()),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate xTuring finetuning inputs without starting training."
    )
    parser.add_argument("--kind", required=True, choices=["instruction", "preference", "text"])
    parser.add_argument(
        "--dataset",
        required=True,
        help="Local dataset path accepted by the selected training kind.",
    )
    parser.add_argument("--model-key", help="Optional xTuring model key to inspect.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        report: Dict[str, Any] = {
            "dataset": summarize_dataset(args.kind, args.dataset),
        }

        if args.model_key:
            report["finetuning_config"] = load_finetuning_config(args.model_key)
    except Exception as exc:  # pragma: no cover - CLI convenience path
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        dataset = report["dataset"]
        print(f"kind: {dataset['kind']}")
        print(f"rows: {dataset['rows']}")
        print(f"columns: {', '.join(dataset['columns'])}")
        print(f"sample_keys: {', '.join(dataset['sample_keys']) if dataset['sample_keys'] else '(empty)'}")
        if "finetuning_config" in report:
            config = report["finetuning_config"]
            print(f"model_key: {args.model_key}")
            print(f"optimizer_name: {config.get('optimizer_name')}")
            print(f"batch_size: {config.get('batch_size')}")
            print(f"max_length: {config.get('max_length')}")
            print(f"use_deepspeed: {config.get('use_deepspeed', False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
