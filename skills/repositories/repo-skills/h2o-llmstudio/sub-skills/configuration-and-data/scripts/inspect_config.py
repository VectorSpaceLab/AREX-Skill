#!/usr/bin/env python3
"""Inspect and round-trip an H2O LLM Studio experiment YAML config."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

from llm_studio.src.utils.config_utils import (
    convert_cfg_base_to_nested_dictionary,
    load_config_yaml,
    save_config_yaml,
)

SECTION_FIELDS: dict[str, tuple[str, ...]] = {
    "dataset": (
        "train_dataframe",
        "validation_strategy",
        "validation_dataframe",
        "validation_size",
        "prompt_column",
        "answer_column",
        "rejected_prompt_column",
        "rejected_answer_column",
        "system_column",
        "parent_id_column",
        "id_column",
        "num_classes",
    ),
    "tokenizer": (
        "max_length",
        "add_prompt_answer_tokens",
        "padding_quantile",
        "tokenizer_kwargs",
    ),
    "architecture": (
        "backbone_dtype",
        "pretrained",
        "gradient_checkpointing",
        "intermediate_dropout",
        "pretrained_weights",
    ),
    "training": (
        "loss_function",
        "optimizer",
        "learning_rate",
        "batch_size",
        "epochs",
        "lora",
        "use_dora",
        "use_rslora",
        "save_checkpoint",
    ),
    "augmentation": (
        "token_mask_probability",
        "skip_parent_probability",
        "random_parent_probability",
        "neftune_noise_alpha",
    ),
    "prediction": (
        "metric",
        "batch_size_inference",
        "do_sample",
        "temperature",
        "num_beams",
        "max_length_inference",
    ),
    "environment": (
        "gpus",
        "mixed_precision",
        "mixed_precision_dtype",
        "use_deepspeed",
        "deepspeed_method",
        "number_of_workers",
        "seed",
    ),
    "logging": ("logger", "log_step_size", "wandb_project", "wandb_entity"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Load an H2O LLM Studio YAML config, check the resolved schema, "
            "and verify a safe save/load round-trip."
        )
    )
    parser.add_argument("--config", required=True, help="Path to a YAML config file.")
    parser.add_argument(
        "--root",
        default=".",
        help=(
            "Project/runtime root used to resolve relative paths and local assets "
            "while loading the config. Defaults to the current directory."
        ),
    )
    parser.add_argument(
        "--expect-problem-type",
        help="Fail if the resolved config problem_type differs from this value.",
    )
    parser.add_argument(
        "--write-roundtrip",
        help="Optional output path for a normalized YAML copy. No file is written unless this is provided.",
    )
    parser.add_argument(
        "--check-data",
        action="store_true",
        help="Also run the config object's built-in checks, which may read local dataset files.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the normalized config dictionary as JSON after validation.",
    )
    return parser.parse_args()


def resolve_under_root(root_arg: str, path_arg: str) -> tuple[Path, Path]:
    root = Path(root_arg).expanduser().resolve()
    raw_path = Path(path_arg).expanduser()
    path = raw_path if raw_path.is_absolute() else root / raw_path
    return root, path.resolve()


def normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): normalize(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize(val) for val in value]
    return value


def find_unknown_keys(raw: Any, normalized_config: Any, prefix: str = "") -> list[str]:
    if not isinstance(raw, dict) or not isinstance(normalized_config, dict):
        return []

    unknown: list[str] = []
    for key, raw_value in raw.items():
        key_str = str(key)
        current = f"{prefix}.{key_str}" if prefix else key_str
        if key_str not in normalized_config:
            unknown.append(current)
            continue
        unknown.extend(find_unknown_keys(raw_value, normalized_config[key_str], current))
    return unknown


def section_summary(cfg: Any, section_name: str) -> str:
    section = getattr(cfg, section_name, None)
    if section is None:
        return "missing"
    parts: list[str] = []
    for field in SECTION_FIELDS[section_name]:
        if hasattr(section, field):
            parts.append(f"{field}={getattr(section, field)!r}")
    return ", ".join(parts) if parts else "no public summary fields"


def print_check_results(results: dict[str, list[Any]]) -> bool:
    titles = results.get("title", [])
    messages = results.get("message", [])
    types = results.get("type", [])
    if not titles:
        print("config_checks: ok")
        return False

    has_error = False
    print("config_checks:")
    for level, title, message in zip(types, titles, messages, strict=False):
        has_error = has_error or level == "error"
        print(f"  - [{level}] {title}: {message}")
    return has_error


def main() -> int:
    args = parse_args()
    root, config_path = resolve_under_root(args.root, args.config)
    if not root.exists():
        print(f"Root does not exist: {root}", file=sys.stderr)
        return 2
    if not config_path.is_file():
        print(f"Config file does not exist: {config_path}", file=sys.stderr)
        return 2

    os.chdir(root)

    raw_yaml = yaml.safe_load(config_path.read_text())
    if not isinstance(raw_yaml, dict):
        print("Config YAML must contain a top-level mapping.", file=sys.stderr)
        return 2

    cfg = load_config_yaml(str(config_path))
    normalized_cfg = normalize(convert_cfg_base_to_nested_dictionary(cfg))
    unknown_keys = find_unknown_keys(raw_yaml, normalized_cfg)

    with tempfile.TemporaryDirectory(prefix="llmstudio-config-roundtrip-") as tmpdir:
        tmp_path = Path(tmpdir) / "roundtrip.yaml"
        save_config_yaml(str(tmp_path), cfg)
        roundtrip_cfg = load_config_yaml(str(tmp_path))
        normalized_roundtrip = normalize(convert_cfg_base_to_nested_dictionary(roundtrip_cfg))

    roundtrip_ok = normalized_cfg == normalized_roundtrip

    expected = args.expect_problem_type
    expected_ok = expected is None or cfg.problem_type == expected

    if args.write_roundtrip:
        output_path = Path(args.write_roundtrip).expanduser()
        output_path = output_path if output_path.is_absolute() else root / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_config_yaml(str(output_path), cfg)

    print(f"config: {config_path}")
    print(f"root: {root}")
    print(f"problem_type: {cfg.problem_type}")
    print(f"config_class: {type(cfg).__module__}.{type(cfg).__name__}")
    print(f"round_trip: {'ok' if roundtrip_ok else 'changed'}")
    print(f"unknown_keys: {', '.join(unknown_keys) if unknown_keys else 'none'}")
    if expected is not None:
        print(f"expected_problem_type: {expected} ({'ok' if expected_ok else 'mismatch'})")
    if args.write_roundtrip:
        print(f"roundtrip_written: {output_path}")

    for section_name in SECTION_FIELDS:
        print(f"{section_name}: {section_summary(cfg, section_name)}")

    has_check_error = False
    if args.check_data:
        try:
            has_check_error = print_check_results(cfg.check())
        except Exception as exc:  # noqa: BLE001 - script should report validation failures cleanly.
            print(f"config_checks: failed: {exc}", file=sys.stderr)
            has_check_error = True

    if args.json:
        print(json.dumps(normalized_cfg, indent=2, sort_keys=True, default=str))

    if not roundtrip_ok:
        print("Round-trip changed the normalized config.", file=sys.stderr)
        return 1
    if unknown_keys:
        print("Unknown config keys were found; fix or intentionally remove them.", file=sys.stderr)
        return 1
    if not expected_ok:
        print("Resolved problem_type does not match expected value.", file=sys.stderr)
        return 1
    if has_check_error:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
