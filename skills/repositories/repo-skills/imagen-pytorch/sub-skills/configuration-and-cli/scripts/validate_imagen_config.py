#!/usr/bin/env python3
"""Static validator for imagen-pytorch CLI JSON configs.

This script intentionally avoids importing imagen_pytorch, torch, datasets, or
transformers. It checks the config assertions that can be proven from the public
CLI/config source without loading datasets, checkpoints, T5 models, or training.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable

ORIGINAL_ONLY_KEYS = {
    "timesteps",
    "noise_schedules",
    "loss_type",
    "pred_objectives",
    "min_snr_loss_weight",
    "min_snr_gamma",
}
ELUCIDATED_HPARAM_KEYS = {
    "num_sample_steps",
    "sigma_min",
    "sigma_max",
    "sigma_data",
    "rho",
    "P_mean",
    "P_std",
    "S_churn",
    "S_tmin",
    "S_tmax",
    "S_noise",
}
NOISE_SCHEDULES = {"cosine", "linear"}
LOSS_TYPES = {"l1", "l2", "huber"}


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def as_list(value: Any) -> list[Any] | None:
    if isinstance(value, list):
        return value
    return None


class Result:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)

    @property
    def ok(self) -> bool:
        return not self.errors


def require_mapping(result: Result, obj: Any, path: str) -> dict[str, Any] | None:
    if not isinstance(obj, dict):
        result.error(f"{path} must be a JSON object")
        return None
    return obj


def require_key(result: Result, obj: dict[str, Any], key: str, path: str) -> Any:
    if key not in obj:
        result.error(f"missing required key {path}.{key}" if path else f"missing required key {key}")
        return None
    return obj[key]


def check_positive_int(result: Result, value: Any, path: str, *, required: bool = False) -> None:
    if value is None and not required:
        return
    if not is_int(value):
        result.error(f"{path} must be an integer")
    elif value <= 0:
        result.error(f"{path} must be a positive integer")


def check_scalar_or_len(result: Result, value: Any, path: str, n: int, *, allowed_values: set[str] | None = None) -> None:
    values: Iterable[Any]
    if isinstance(value, list):
        if len(value) != n:
            result.error(f"{path} list length {len(value)} must match number of unets {n}")
        values = value
    else:
        values = [value]
    if allowed_values is not None:
        for item in values:
            if item not in allowed_values:
                result.error(f"{path} value {item!r} must be one of {sorted(allowed_values)}")


def check_optional_numeric_schedule(result: Result, imagen: dict[str, Any], key: str, n: int) -> None:
    if key not in imagen:
        return
    value = imagen[key]
    values = value if isinstance(value, list) else [value]
    if isinstance(value, list) and len(value) != n:
        result.error(f"imagen.{key} list length {len(value)} must match number of unets {n}")
    for item in values:
        if item is not None and not is_number(item):
            result.error(f"imagen.{key} values must be numeric or null")


def validate_unets(result: Result, unets: Any) -> int:
    if not isinstance(unets, list) or not unets:
        result.error("imagen.unets must be a non-empty list")
        return 0
    for i, unet in enumerate(unets):
        path = f"imagen.unets[{i}]"
        if not isinstance(unet, dict):
            result.error(f"{path} must be an object")
            continue
        if unet.get("is_null") is True:
            extra = sorted(set(unet) - {"is_null"})
            if extra:
                result.warn(f"{path} is a NullUnetConfig; extra keys are ignored or invalid: {extra}")
            continue
        dim = unet.get("dim")
        if not is_int(dim) or dim <= 0:
            result.error(f"{path}.dim must be a positive integer unless is_null is true")
        dim_mults = unet.get("dim_mults")
        if not isinstance(dim_mults, list) or not dim_mults:
            result.error(f"{path}.dim_mults must be a non-empty list of positive integers")
        else:
            for j, item in enumerate(dim_mults):
                if not is_int(item) or item <= 0:
                    result.error(f"{path}.dim_mults[{j}] must be a positive integer")
        for boolish in ("layer_attns", "layer_cross_attns"):
            if boolish in unet:
                v = unet[boolish]
                if not isinstance(v, (bool, list)):
                    result.warn(f"{path}.{boolish} is usually a boolean or list of booleans")
        if "channels" in unet and (not is_int(unet["channels"]) or unet["channels"] <= 0):
            result.error(f"{path}.channels must be a positive integer when supplied")
    return len(unets)


def validate_imagen(result: Result, config_type: str, imagen: Any, *, mode: str, unet_number: int | None) -> int:
    imagen = require_mapping(result, imagen, "imagen")
    if imagen is None:
        return 0

    unets = require_key(result, imagen, "unets", "imagen")
    image_sizes = require_key(result, imagen, "image_sizes", "imagen")
    n_unets = validate_unets(result, unets)

    if not isinstance(image_sizes, list) or not image_sizes:
        result.error("imagen.image_sizes must be a non-empty list for CLI train")
    else:
        if n_unets and len(image_sizes) != n_unets:
            result.error(f"imagen.image_sizes length {len(image_sizes)} must equal number of unets {n_unets}")
        for i, size in enumerate(image_sizes):
            if not is_int(size) or size <= 0:
                result.error(f"imagen.image_sizes[{i}] must be a positive integer")

    if unet_number is not None:
        if unet_number < 1 or unet_number >= 3:
            result.error("CLI train --unet must satisfy [1<=x<3], so only 1 or 2 are accepted")
        if isinstance(image_sizes, list) and unet_number > len(image_sizes):
            result.error(f"--unet {unet_number} exceeds imagen.image_sizes length {len(image_sizes)}")

    channels = imagen.get("channels", 3)
    if not is_int(channels):
        result.error("imagen.channels must be an integer when supplied")
    elif not (1 <= channels <= 4):
        result.error("imagen.channels must be in the CLI-supported range 1..4")
    elif channels == 2:
        result.warn("CLI channel 2 is intended as LA but the package branch has an assignment typo; prefer 1, 3, or 4")

    if "random_crop_sizes" in imagen:
        rcs = imagen["random_crop_sizes"]
        if rcs is not None:
            if not isinstance(rcs, list):
                result.error("imagen.random_crop_sizes must be null or a list")
            else:
                if n_unets and len(rcs) != n_unets:
                    result.error(f"imagen.random_crop_sizes length {len(rcs)} must equal number of unets {n_unets}")
                if rcs and rcs[0] is not None:
                    result.error("imagen.random_crop_sizes[0] must be null; base unet should not random-crop")

    if config_type == "original":
        if "loss_type" in imagen and imagen["loss_type"] not in LOSS_TYPES:
            result.error(f"imagen.loss_type must be one of {sorted(LOSS_TYPES)}")
        if "noise_schedules" in imagen:
            ns = imagen["noise_schedules"]
            values = ns if isinstance(ns, list) else [ns]
            for item in values:
                if item not in NOISE_SCHEDULES:
                    result.error(f"imagen.noise_schedules value {item!r} must be one of {sorted(NOISE_SCHEDULES)}")
            if isinstance(ns, list) and n_unets and len(ns) > n_unets:
                result.warn("imagen.noise_schedules has more entries than unets; extras are not useful")
        if "timesteps" in imagen:
            ts = imagen["timesteps"]
            values = ts if isinstance(ts, list) else [ts]
            if isinstance(ts, list) and n_unets and len(ts) != n_unets:
                result.error(f"imagen.timesteps list length {len(ts)} must equal number of unets {n_unets}")
            for item in values:
                if not is_int(item) or item <= 0:
                    result.error("imagen.timesteps values must be positive integers")
    else:
        suspicious = sorted(ORIGINAL_ONLY_KEYS & set(imagen))
        if suspicious:
            result.warn(f"elucidated configs should not usually include original-only keys: {suspicious}")
        for key in ELUCIDATED_HPARAM_KEYS:
            check_optional_numeric_schedule(result, imagen, key, n_unets)

    if n_unets > 2:
        result.warn("config has more than two unets, but CLI train --unet accepts only 1 or 2")

    return n_unets


def validate_trainer(result: Result, trainer: Any, *, mode: str) -> dict[str, Any]:
    trainer = require_mapping(result, trainer, "trainer")
    if trainer is None:
        return {}
    for key in ("lr", "eps", "warmup_steps", "cosine_decay_max_steps"):
        if key not in trainer:
            continue
        value = trainer[key]
        values = value if isinstance(value, list) else [value]
        for item in values:
            if item is not None and not is_number(item):
                result.error(f"trainer.{key} values must be numeric or null")
    for key in ("beta1", "beta2", "max_grad_norm", "split_valid_fraction"):
        if key in trainer and trainer[key] is not None and not is_number(trainer[key]):
            result.error(f"trainer.{key} must be numeric or null")
    for key in ("use_ema", "group_wd_params", "split_valid_from_train", "fp16", "split_batches", "verbose"):
        if key in trainer and not isinstance(trainer[key], bool):
            result.error(f"trainer.{key} must be boolean when supplied")
    return trainer


def validate_dataset_and_cli(result: Result, cfg: dict[str, Any], trainer: dict[str, Any], *, mode: str) -> None:
    dataset = require_key(result, cfg, "dataset", "")
    dataset = require_mapping(result, dataset, "dataset") if dataset is not None else None
    if dataset is not None:
        if "batch_size" not in dataset:
            result.error("dataset.batch_size is required by imagen train")
        else:
            check_positive_int(result, dataset["batch_size"], "dataset.batch_size")

    dataset_name = cfg.get("dataset_name")
    if not isinstance(dataset_name, str) or not dataset_name.strip():
        result.error("dataset_name must be a non-empty string")

    if "checkpoint_path" not in cfg:
        result.error("checkpoint_path is required by imagen train")
    elif not isinstance(cfg["checkpoint_path"], str) or not cfg["checkpoint_path"].strip():
        result.error("checkpoint_path must be a non-empty string")
    else:
        parent = os.path.dirname(cfg["checkpoint_path"])
        if parent and not os.path.isdir(parent):
            result.warn(f"checkpoint_path parent directory does not exist yet: {parent}")

    url_label = cfg.get("url_label")
    image_label = cfg.get("image_label")
    text_label = cfg.get("text_label")
    if url_label is not None and not isinstance(url_label, str):
        result.error("url_label must be a string or null")
    if image_label is not None and not isinstance(image_label, str):
        result.error("image_label must be a string or null")
    if url_label is None and not image_label:
        result.warn("url_label is null, so image_label should name a dataset image field for CLI collator use")
    if not isinstance(text_label, str) or not text_label:
        result.warn("text_label should be a non-empty string; the CLI collator encodes item[text_label]")

    for key in ("validate_at_every", "sample_at_every", "save_at_every"):
        if key in cfg:
            check_positive_int(result, cfg[key], key)

    if "sample_at_every" in cfg:
        sample_texts = cfg.get("sample_texts")
        if not isinstance(sample_texts, list):
            result.error("sample_texts must be a list when sample_at_every is set")
        elif not sample_texts:
            result.error("sample_texts must not be empty when sample_at_every is set")
        elif not all(isinstance(text, str) and text for text in sample_texts):
            result.error("sample_texts entries must be non-empty strings")
        if "save_at_every" not in cfg:
            result.error("save_at_every should be present and positive when CLI in-loop sampling is enabled")
    elif "sample_texts" in cfg:
        result.warn("sample_texts is present without sample_at_every; CLI train will not enable should_sample")

    if mode == "train":
        if "save_at_every" not in cfg:
            result.error("CLI train can hit modulo-by-zero unless save_at_every is present and positive")
        if not trainer.get("split_valid_from_train", False):
            result.error("CLI train can hit modulo-by-zero unless trainer.split_valid_from_train is true with validate_at_every present")
        if "validate_at_every" not in cfg:
            result.error("CLI train with validation split should include positive validate_at_every")


def validate_config(cfg: Any, *, mode: str, unet_number: int | None) -> Result:
    result = Result()
    cfg = require_mapping(result, cfg, "config")
    if cfg is None:
        return result

    config_type = require_key(result, cfg, "type", "")
    if config_type not in {"original", "elucidated"}:
        result.error('type must be exactly "original" or "elucidated"')
        config_type = "original"

    imagen = require_key(result, cfg, "imagen", "")
    trainer_obj = require_key(result, cfg, "trainer", "")
    validate_imagen(result, str(config_type), imagen, mode=mode, unet_number=unet_number)
    trainer = validate_trainer(result, trainer_obj, mode=mode)
    validate_dataset_and_cli(result, cfg, trainer, mode=mode)

    result.note("static validation only; no dataset, checkpoint, T5, CUDA, or training was loaded")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Static preflight validator for imagen-pytorch CLI JSON configs")
    parser.add_argument("config", type=Path, help="Path to imagen config JSON")
    parser.add_argument("--mode", choices=("schema", "train"), default="schema", help="schema checks only, or stricter CLI train preflight")
    parser.add_argument("--unet", type=int, default=None, help="Target CLI train --unet value to validate")
    parser.add_argument("--strict-warnings", action="store_true", help="Treat warnings as a non-zero result")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)

    try:
        data = json.loads(args.config.read_text())
    except FileNotFoundError:
        print(f"ERROR: config file not found: {args.config}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON at line {exc.lineno} column {exc.colno}: {exc.msg}", file=sys.stderr)
        return 2

    result = validate_config(data, mode=args.mode, unet_number=args.unet)
    payload = {
        "ok": result.ok and not (args.strict_warnings and result.warnings),
        "mode": args.mode,
        "errors": result.errors,
        "warnings": result.warnings,
        "notes": result.notes,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if result.errors:
            print("Errors:")
            for msg in result.errors:
                print(f"  - {msg}")
        if result.warnings:
            print("Warnings:")
            for msg in result.warnings:
                print(f"  - {msg}")
        if result.notes:
            print("Notes:")
            for msg in result.notes:
                print(f"  - {msg}")
        if payload["ok"]:
            print("OK: static imagen config preflight passed")
        else:
            print("FAILED: static imagen config preflight found blocking issues")

    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
