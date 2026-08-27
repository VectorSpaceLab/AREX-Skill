#!/usr/bin/env python3
"""Print or write a CPU-safe Towhee TrainingConfig template.

By default this script uses only Python's standard library and does not import
Towhee, torch, torchvision, or torchmetrics. Use --check-imports only when the
current environment is intentionally prepared for Towhee's optional training
stack and any import-time dependency side effects are acceptable.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict


CONFIG: Dict[str, Any] = {
    "train": {
        "output_dir": "./towhee-training-output",
        "overwrite_output_dir": True,
        "eval_strategy": "no",
        "eval_steps": None,
        "batch_size": 2,
        "val_batch_size": -1,
        "seed": 42,
        "epoch_num": 1,
        "dataloader_pin_memory": False,
        "dataloader_drop_last": False,
        "dataloader_num_workers": 0,
        "print_steps": 1,
        "load_best_model_at_end": False,
        "freeze_bn": False,
    },
    "learning": {
        "loss": "CrossEntropyLoss",
        "optimizer": {"name_": "AdamW", "lr": 0.001},
        "lr_scheduler_type": "linear",
        "warmup_ratio": 0.0,
        "warmup_steps": 0,
    },
    "metrics": {"metric": "Accuracy"},
    "logging": {},
    "callback": {
        "early_stopping": "no",
        "model_checkpoint": "no",
        "tensorboard": None,
    },
    "device": {"device_str": "cpu"},
}


SECTION_ORDER = ["train", "learning", "metrics", "logging", "callback", "device"]


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    safe = text.replace("_", "").replace("-", "").replace(".", "").replace("/", "")
    if text in {"no", "null", "None"} or not safe.isalnum() or text == "":
        return json.dumps(text)
    return text


def _dump_yaml_mapping(mapping: Dict[str, Any], indent: int = 0) -> str:
    lines = []
    prefix = " " * indent
    for key, value in mapping.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            if value:
                lines.append(_dump_yaml_mapping(value, indent + 2))
            else:
                lines[-1] = f"{prefix}{key}: {{}}"
        else:
            lines.append(f"{prefix}{key}: {_yaml_scalar(value)}")
    return "\n".join(lines)


def render_yaml(config: Dict[str, Any]) -> str:
    ordered = {section: config[section] for section in SECTION_ORDER if section in config}
    return _dump_yaml_mapping(ordered) + "\n"


def render_json(config: Dict[str, Any]) -> str:
    return json.dumps(config, indent=2, sort_keys=False) + "\n"


def check_imports() -> None:
    """Explicit optional check that imports Towhee's trainer stack."""
    from towhee.trainer.training_config import TrainingConfig  # pylint: disable=import-outside-toplevel

    cfg = TrainingConfig()
    data = cfg.to_dict()
    required = {"output_dir", "optimizer", "loss", "lr_scheduler_type", "device_str"}
    missing = sorted(required.difference(data))
    if missing:
        raise RuntimeError(f"TrainingConfig import succeeded but fields are missing: {missing}")
    print("Towhee TrainingConfig import check passed.", file=sys.stderr)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a CPU-safe Towhee TrainingConfig YAML or JSON template without importing torch by default."
    )
    parser.add_argument("--format", choices=("yaml", "json"), default="yaml", help="Template format to print/write.")
    parser.add_argument("--output", type=Path, help="Optional file path to write. The template is always printed too.")
    parser.add_argument(
        "--check-imports",
        action="store_true",
        help="Also import Towhee's optional trainer TrainingConfig. This may import torch and trigger Towhee dependency side effects.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    text = render_yaml(CONFIG) if args.format == "yaml" else render_json(CONFIG)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")

    sys.stdout.write(text)

    if args.check_imports:
        check_imports()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
