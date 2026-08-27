#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# DeepSpeed Team
"""Safely validate DeepSpeed training config JSON/HJSON without launching training."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class DuplicateKeyError(ValueError):
    """Raised when strict JSON parsing sees the same key twice."""


def no_duplicate_object_pairs(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate key: {key}")
        result[key] = value
    return result


def load_config(path: Path) -> Tuple[Dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    try:
        parsed = json.loads(text, object_pairs_hook=no_duplicate_object_pairs)
        if not isinstance(parsed, dict):
            raise ValueError("top-level config must be an object")
        return parsed, "json"
    except DuplicateKeyError:
        raise
    except json.JSONDecodeError as json_error:
        try:
            import hjson  # type: ignore
        except ImportError as import_error:
            raise ValueError(
                f"invalid JSON ({json_error}); install hjson to parse HJSON-style configs"
            ) from import_error
        parsed = hjson.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError("top-level config must be an object")
        return parsed, "hjson"


def as_positive_int(config: Dict[str, Any], key: str, errors: List[str]) -> Optional[int]:
    if key not in config or config[key] is None:
        return None
    value = config[key]
    if isinstance(value, bool) or not isinstance(value, int):
        errors.append(f"{key} must be a positive integer")
        return None
    if value <= 0:
        errors.append(f"{key} must be greater than zero")
        return None
    return value


def check_batch(config: Dict[str, Any], world_size: int, errors: List[str], warnings: List[str]) -> None:
    train_batch = as_positive_int(config, "train_batch_size", errors)
    micro_batch = as_positive_int(config, "train_micro_batch_size_per_gpu", errors)
    grad_acc = as_positive_int(config, "gradient_accumulation_steps", errors)

    specified = [value is not None for value in (train_batch, micro_batch, grad_acc)].count(True)
    if specified == 0 or (specified == 1 and grad_acc is not None):
        errors.append("provide train_batch_size or train_micro_batch_size_per_gpu, preferably two batch fields")
        return

    if train_batch is not None and micro_batch is not None and grad_acc is not None:
        expected = micro_batch * grad_acc * world_size
        if train_batch != expected:
            errors.append(
                "train_batch_size must equal train_micro_batch_size_per_gpu * "
                f"gradient_accumulation_steps * world_size ({train_batch} != {micro_batch} * {grad_acc} * {world_size})"
            )
        return

    if train_batch is not None and micro_batch is not None:
        denominator = micro_batch * world_size
        if train_batch % denominator != 0:
            errors.append(
                f"cannot infer gradient_accumulation_steps: train_batch_size {train_batch} is not divisible by "
                f"train_micro_batch_size_per_gpu * world_size ({denominator})"
            )
        else:
            warnings.append(f"inferred gradient_accumulation_steps={train_batch // denominator}")
    elif train_batch is not None and grad_acc is not None:
        denominator = grad_acc * world_size
        if train_batch % denominator != 0:
            errors.append(
                f"cannot infer train_micro_batch_size_per_gpu: train_batch_size {train_batch} is not divisible by "
                f"gradient_accumulation_steps * world_size ({denominator})"
            )
        else:
            warnings.append(f"inferred train_micro_batch_size_per_gpu={train_batch // denominator}")
    elif micro_batch is not None and grad_acc is not None:
        warnings.append(f"inferred train_batch_size={micro_batch * grad_acc * world_size}")
    elif train_batch is not None:
        if train_batch % world_size != 0:
            errors.append(f"cannot infer micro batch: train_batch_size {train_batch} is not divisible by world_size {world_size}")
        else:
            warnings.append("inferred gradient_accumulation_steps=1")
            warnings.append(f"inferred train_micro_batch_size_per_gpu={train_batch // world_size}")
    elif micro_batch is not None:
        warnings.append("inferred gradient_accumulation_steps=1")
        warnings.append(f"inferred train_batch_size={micro_batch * world_size}")


def check_zero(config: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    zero_config = config.get("zero_optimization", {})
    if isinstance(zero_config, bool):
        warnings.append("zero_optimization boolean format is deprecated; use an object with stage")
        return
    if zero_config is None:
        return
    if not isinstance(zero_config, dict):
        errors.append("zero_optimization must be an object, boolean, or omitted")
        return

    stage = zero_config.get("stage", 0)
    if isinstance(stage, bool) or stage not in (0, 1, 2, 3):
        errors.append("zero_optimization.stage must be one of 0, 1, 2, 3")

    deprecated = {
        "cpu_offload": "offload_optimizer",
        "cpu_offload_param": "offload_param",
        "cpu_offload_use_pin_memory": "pin_memory under offload_param/offload_optimizer",
        "stage3_gather_fp16_weights_on_model_save": "stage3_gather_16bit_weights_on_model_save",
    }
    for old_key, new_key in deprecated.items():
        if old_key in zero_config:
            warnings.append(f"{old_key} is deprecated; prefer {new_key}")

    if "offload_param" in zero_config and stage != 3:
        errors.append("offload_param is valid only with ZeRO stage 3")

    for offload_key in ("offload_param", "offload_optimizer"):
        value = zero_config.get(offload_key)
        if value is None:
            continue
        if not isinstance(value, dict):
            errors.append(f"{offload_key} must be an object")
            continue
        device = value.get("device")
        if device not in ("cpu", "nvme"):
            errors.append(f"{offload_key}.device should be 'cpu' or 'nvme'")
        if device == "nvme" and not value.get("nvme_path"):
            warnings.append(f"{offload_key}.device is nvme but nvme_path is not set")

    if stage == 3 and not zero_config.get("stage3_gather_16bit_weights_on_model_save", False):
        warnings.append("ZeRO-3 save_16bit_model requires stage3_gather_16bit_weights_on_model_save=true for consolidated weights")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="DeepSpeed config JSON/HJSON path")
    parser.add_argument("--world-size", type=int, default=1, help="Expected distributed world size for batch validation")
    args = parser.parse_args()

    if args.world_size <= 0:
        print("ERROR: --world-size must be greater than zero", file=sys.stderr)
        return 2

    errors: List[str] = []
    warnings: List[str] = []
    try:
        config, parser_name = load_config(args.config)
    except Exception as error:  # noqa: BLE001 - command-line validator should surface concise errors.
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    check_batch(config, args.world_size, errors, warnings)
    check_zero(config, errors, warnings)

    print(f"Parsed as {parser_name}: {args.config}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors:
        return 1
    print("OK: no blocking config issues found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
