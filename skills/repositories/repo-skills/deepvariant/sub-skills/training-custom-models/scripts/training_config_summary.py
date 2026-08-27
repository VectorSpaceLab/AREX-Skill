#!/usr/bin/env python3
"""Summarize DeepVariant r1.10 training configs and metadata.

This helper intentionally avoids importing DeepVariant, TensorFlow, Keras,
ml_collections, Apache Beam, protobuf, or genomics IO libraries. It is a safe
planning aid for reviewing distilled config names, dataset pbtxt scalar fields,
and example_info JSON shape/channel metadata.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

BASE_CHANNELS = [
    "read_base",
    "base_quality",
    "mapping_quality",
    "strand",
    "read_supports_variant",
    "base_differs_from_ref",
]

CHANNEL_ENUM_TO_NAME = {
    1: "read_base",
    2: "base_quality",
    3: "mapping_quality",
    4: "strand",
    5: "read_supports_variant",
    6: "base_differs_from_ref",
    7: "haplotype",
    8: "allele_frequency",
    9: "diff_channels_alternate_allele_1",
    10: "diff_channels_alternate_allele_2",
    11: "read_mapping_percent",
    12: "avg_base_quality",
    13: "identity",
    14: "gap_compressed_identity",
    15: "gc_content",
    16: "is_homopolymer",
    17: "homopolymer_weighted",
    18: "blank",
    19: "insert_size",
    20: "base_channels_alternate_allele_1",
    21: "base_channels_alternate_allele_2",
    22: "mean_coverage",
    23: "base_methylation",
    24: "base_6ma",
    25: "read_supports_variant_fuzzy",
    26: "supplementary_alignment",
    27: "allele_sample_probability",
    28: "homopolymer_insertion_quality",
    29: "homopolymer_deletion_quality",
    30: "inter_homopolymer_insertion_quality",
}

CONFIGS = {
    "base": {
        "use": "Generic starting point; commonly overridden for tutorials.",
        "optimizer": "rmsprop",
        "best_checkpoint_metric": "tune/f1_weighted",
        "batch_size": 16384,
        "num_epochs": 10,
        "init_checkpoint": "empty by default",
        "notes": "Requires explicit train_dataset_pbtxt and tune_dataset_pbtxt.",
    },
    "base+test": {
        "use": "Tiny native-test style smoke config only.",
        "optimizer": "inherits base",
        "best_checkpoint_metric": "tune/f1_weighted",
        "batch_size": 4,
        "num_epochs": 2,
        "init_checkpoint": "empty",
        "notes": "Uses limit=50 and is not a production training recipe.",
    },
    "wgs": {
        "use": "Whole-genome short-read training.",
        "optimizer": "sgd",
        "best_checkpoint_metric": "tune/f1_weighted",
        "batch_size": 16384,
        "num_epochs": 10,
        "init_checkpoint": "empty by default",
        "notes": "Uses EMA and expects large WGS-scale labeled datasets.",
    },
    "exome": {
        "use": "Whole-exome training or fine-tuning.",
        "optimizer": "sgd",
        "best_checkpoint_metric": "tune/f1_weighted",
        "batch_size": 16384,
        "num_epochs": 20,
        "init_checkpoint": "expected warm-start path",
        "notes": "Verify capture/confident-region design before tuning.",
    },
    "pacbio": {
        "use": "PacBio long-read training.",
        "optimizer": "adam",
        "best_checkpoint_metric": "tune/categorical_accuracy",
        "batch_size": 16384,
        "num_epochs": 8,
        "init_checkpoint": "expected warm-start path",
        "notes": "Requires assay-specific validation before reusing other checkpoints.",
    },
    "ont": {
        "use": "ONT training.",
        "optimizer": "adam",
        "best_checkpoint_metric": "tune/categorical_accuracy",
        "batch_size": 16384,
        "num_epochs": 8,
        "init_checkpoint": "empty by default",
        "notes": "Inherits PacBio-style hyperparameters in DeepVariant r1.10.",
    },
    "hybrid": {
        "use": "Hybrid PacBio + Illumina training.",
        "optimizer": "adam",
        "best_checkpoint_metric": "tune/categorical_accuracy",
        "batch_size": 16384,
        "num_epochs": 10,
        "init_checkpoint": "expected warm-start path",
        "notes": "Keep hybrid evidence separate from single-assay validation.",
    },
    "rnaseq": {
        "use": "RNA-seq fine-tuning.",
        "optimizer": "sgd",
        "best_checkpoint_metric": "tune/f1_weighted",
        "batch_size": 8192,
        "num_epochs": 5,
        "init_checkpoint": "expected warm-start path",
        "notes": "Uses smaller batch size and low learning rate for fine-tuning.",
    },
    "pangenome_wgs": {
        "use": "Pangenome-aware WGS training.",
        "optimizer": "sgd",
        "best_checkpoint_metric": "tune/f1_weighted",
        "batch_size": 16384,
        "num_epochs": 10,
        "init_checkpoint": "inherits WGS default",
        "notes": "Requires pangenome-aware evidence and validation planning.",
    },
}

REQUIRED_DATASET_FIELDS = ("name", "tfrecord_path", "num_examples")


def parse_pbtxt_scalars(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    pattern = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*?)\s*$")
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = pattern.match(line)
        if not match:
            continue
        key, raw_value = match.groups()
        value = raw_value.split("#", 1)[0].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key] = value
    return values


def load_example_info(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if not path.exists():
        return None, [f"example info JSON does not exist: {path}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return None, [f"invalid JSON: {error}"]
    if not isinstance(payload, dict):
        return None, ["top-level JSON value must be an object"]
    shape = payload.get("shape")
    channels = payload.get("channels")
    if not isinstance(shape, list) or len(shape) != 3:
        errors.append("shape must be a three-element list [height, width, channels]")
    elif not all(isinstance(value, int) and value > 0 for value in shape):
        errors.append("shape values must be positive integers")
    if not isinstance(channels, list) or not channels:
        errors.append("channels must be a non-empty list")
    elif isinstance(shape, list) and len(shape) == 3 and shape[2] != len(channels):
        errors.append(
            f"shape channel dimension ({shape[2]}) does not match channel count ({len(channels)})"
        )
    return payload, errors


def channel_names(channels: list[Any]) -> list[str]:
    names: list[str] = []
    for channel in channels:
        if isinstance(channel, int):
            names.append(CHANNEL_ENUM_TO_NAME.get(channel, f"unknown_enum_{channel}"))
        else:
            names.append(str(channel))
    return names


def command_list_configs(_: argparse.Namespace) -> int:
    for name in sorted(CONFIGS):
        print(f"{name}: {CONFIGS[name]['use']}")
    return 0


def command_show_config(args: argparse.Namespace) -> int:
    config = CONFIGS.get(args.name)
    if not config:
        print(f"Unknown config: {args.name}", file=sys.stderr)
        print("Known configs: " + ", ".join(sorted(CONFIGS)), file=sys.stderr)
        return 2
    print(f"Config: {args.name}")
    for key in (
        "use",
        "optimizer",
        "best_checkpoint_metric",
        "batch_size",
        "num_epochs",
        "init_checkpoint",
        "notes",
    ):
        print(f"{key}: {config[key]}")
    return 0


def command_validate_dataset(args: argparse.Namespace) -> int:
    path = Path(args.pbtxt)
    if not path.exists():
        print(f"ERROR: dataset config does not exist: {path}", file=sys.stderr)
        return 2
    values = parse_pbtxt_scalars(path)
    errors = []
    for field in REQUIRED_DATASET_FIELDS:
        if not values.get(field):
            errors.append(f"missing required field: {field}")
    if values.get("num_examples"):
        try:
            num_examples = int(values["num_examples"])
        except ValueError:
            errors.append("num_examples must be an integer")
        else:
            if num_examples <= 0:
                errors.append("num_examples must be positive")
    if values.get("tfrecord_path") and "tfrecord" not in values["tfrecord_path"]:
        print("WARNING: tfrecord_path does not contain 'tfrecord'; verify this is intentional")
    print(f"Dataset config: {path}")
    for field in REQUIRED_DATASET_FIELDS:
        print(f"{field}: {values.get(field, '<missing>')}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK: required dataset fields are present")
    return 0


def describe_example_info(path: Path, payload: dict[str, Any]) -> list[str]:
    channels = payload.get("channels")
    names = channel_names(channels) if isinstance(channels, list) else []
    lines = [
        f"Example info: {path}",
        f"version: {payload.get('version', '<missing>')}",
        f"shape: {payload.get('shape', '<missing>')}",
        f"channels: {', '.join(names) if names else '<missing>'}",
    ]
    if payload.get("ablation_channels"):
        ablation_names = channel_names(payload["ablation_channels"])
        lines.append(f"ablation_channels: {', '.join(ablation_names)}")
    return lines


def command_inspect_example_info(args: argparse.Namespace) -> int:
    path = Path(args.json_path)
    payload, errors = load_example_info(path)
    if payload is None:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    for line in describe_example_info(path, payload):
        print(line)
    channels = payload.get("channels")
    names = channel_names(channels) if isinstance(channels, list) else []
    for expected_channel in args.expected_channel:
        if expected_channel not in names:
            print(f"WARNING: expected channel not present: {expected_channel}")
    if args.expect_wgs_insert_size:
        expected = BASE_CHANNELS + ["insert_size"]
        missing = [name for name in expected if name not in names]
        if missing:
            print("WARNING: WGS-style BASE_CHANNELS,insert_size is missing: " + ", ".join(missing))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK: example-info shape/channel metadata is structurally valid")
    return 0


def command_compare_example_info(args: argparse.Namespace) -> int:
    left_path = Path(args.left_json)
    right_path = Path(args.right_json)
    left, left_errors = load_example_info(left_path)
    right, right_errors = load_example_info(right_path)
    if left is None or right is None:
        for error in left_errors + right_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    errors = left_errors + right_errors
    warnings: list[str] = []
    left_shape = left.get("shape")
    right_shape = right.get("shape")
    left_channels = left.get("channels")
    right_channels = right.get("channels")
    if left_shape != right_shape:
        errors.append(f"shape differs: {left_shape} != {right_shape}")
    if left_channels != right_channels:
        errors.append(
            "channels differ: "
            f"{channel_names(left_channels) if isinstance(left_channels, list) else left_channels} != "
            f"{channel_names(right_channels) if isinstance(right_channels, list) else right_channels}"
        )
    if left.get("version") != right.get("version"):
        warnings.append(f"version differs: {left.get('version')} != {right.get('version')}")
    print(f"Left: {left_path}")
    print(f"  shape: {left_shape}")
    print(f"  channels: {', '.join(channel_names(left_channels)) if isinstance(left_channels, list) else '<invalid>'}")
    print(f"Right: {right_path}")
    print(f"  shape: {right_shape}")
    print(f"  channels: {', '.join(channel_names(right_channels)) if isinstance(right_channels, list) else '<invalid>'}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK: example-info shape and channels match")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize DeepVariant r1.10 training config and metadata contracts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_configs = subparsers.add_parser("list-configs", help="List distilled config names.")
    list_configs.set_defaults(func=command_list_configs)

    show_config = subparsers.add_parser("show-config", help="Show one config summary.")
    show_config.add_argument("name", help="Config name such as wgs, exome, pacbio, ont, hybrid, rnaseq, or base.")
    show_config.set_defaults(func=command_show_config)

    validate_dataset = subparsers.add_parser(
        "validate-dataset",
        help="Check required dataset_config.pbtxt scalar fields without importing protobuf.",
    )
    validate_dataset.add_argument("pbtxt", help="Path to dataset_config.pbtxt.")
    validate_dataset.set_defaults(func=command_validate_dataset)

    inspect_example = subparsers.add_parser(
        "inspect-example-info",
        help="Inspect example_info JSON shape/channels without TensorFlow.",
    )
    inspect_example.add_argument("json_path", help="Path to example_info.json or model.example_info.json.")
    inspect_example.add_argument(
        "--expected-channel",
        action="append",
        default=[],
        help="Channel name expected to be present; may be repeated.",
    )
    inspect_example.add_argument(
        "--expect-wgs-insert-size",
        action="store_true",
        help="Warn unless BASE_CHANNELS plus insert_size are all present.",
    )
    inspect_example.set_defaults(func=command_inspect_example_info)

    compare_example = subparsers.add_parser(
        "compare-example-info",
        help="Compare two example_info/model.example_info files for shape and channel compatibility.",
    )
    compare_example.add_argument("left_json", help="First example_info JSON path.")
    compare_example.add_argument("right_json", help="Second example_info JSON path.")
    compare_example.set_defaults(func=command_compare_example_info)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
