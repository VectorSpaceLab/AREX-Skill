#!/usr/bin/env python3
"""Validate a DALLE2-pytorch decoder or diffusion-prior training config.

The script imports only the public installed package (`dalle2_pytorch`) and does
not start training or open dataset shards.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from importlib import metadata
from pathlib import Path
from typing import Any, Iterable


PLACEHOLDER_MARKERS = (
    "ABSOLUTE/PATH/TO",
    "<path",
    "<your",
    "YOUR_",
    "your_",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a DALLE2-pytorch training JSON config without launching training.")
    parser.add_argument("--kind", choices=("decoder", "prior"), required=True, help="Config type to validate.")
    parser.add_argument("--config", required=True, help="Path to the JSON config file.")
    return parser


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise ConfigError(f"config file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc

    if not isinstance(data, dict):
        raise ConfigError("top-level JSON value must be an object")
    return data


class ConfigError(Exception):
    """User-facing config validation error."""


def model_to_dict(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    return dict(model)


def as_list(value: Any, *, length: int | None = None) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    if length is None:
        return [value]
    return [value for _ in range(length)]


def has_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return any(marker in value for marker in PLACEHOLDER_MARKERS)
    if isinstance(value, dict):
        return any(has_placeholder(v) for v in value.values())
    if isinstance(value, list):
        return any(has_placeholder(v) for v in value)
    return False


def split_sum(splits: Any) -> float | None:
    if splits is None:
        return None
    return float(splits.train) + float(splits.val) + float(splits.test)


def validate_common_positive(name: str, value: Any, errors: list[str]) -> None:
    try:
        if value is not None and value <= 0:
            errors.append(f"{name} must be positive; got {value!r}")
    except TypeError:
        errors.append(f"{name} must be numeric; got {value!r}")


def validate_decoder(config: Any) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []

    decoder = config.decoder
    data = config.data
    train = config.train
    evaluate = config.evaluate

    unets = list(decoder.unets)
    num_unets = len(unets)
    if num_unets == 0:
        errors.append("decoder.unets must contain at least one UNet config")

    has_image_size = decoder.image_size is not None
    has_image_sizes = decoder.image_sizes is not None
    if has_image_size == has_image_sizes:
        errors.append("decoder must set exactly one of image_size or image_sizes")
    if has_image_sizes and len(list(decoder.image_sizes)) != num_unets:
        errors.append(f"decoder.image_sizes length must equal number of unets ({num_unets})")

    sample_timesteps = as_list(decoder.sample_timesteps, length=num_unets)
    if sample_timesteps and len(sample_timesteps) not in (1, num_unets):
        errors.append(f"decoder.sample_timesteps length should be 1 or number of unets ({num_unets})")
    for idx, steps in enumerate(sample_timesteps, start=1):
        if steps is not None and steps > decoder.timesteps:
            errors.append(f"decoder.sample_timesteps for unet {idx} ({steps}) exceeds decoder.timesteps ({decoder.timesteps})")

    learned_variance = as_list(decoder.learned_variance, length=num_unets)
    if any(bool(v) for v in learned_variance):
        warnings.append("decoder.learned_variance is enabled; DeepSpeed fp16 launches must set it false")

    mask = train.unet_training_mask
    if mask is not None and len(list(mask)) != num_unets:
        errors.append(f"train.unet_training_mask length must equal number of unets ({num_unets})")

    validate_common_positive("data.batch_size", data.batch_size, errors)
    validate_common_positive("train.epochs", train.epochs, errors)
    if data.end_shard < data.start_shard:
        errors.append("data.end_shard must be greater than or equal to data.start_shard")

    if data.resample_train and train.epoch_samples is None:
        errors.append("train.epoch_samples is required when data.resample_train is true")
    if data.resample_train and data.shuffle_train:
        warnings.append("data.shuffle_train and data.resample_train are both true; disable shuffle while debugging resampling")

    split_total = split_sum(data.splits)
    if split_total is not None and not math.isclose(split_total, 1.0, rel_tol=0.0, abs_tol=1e-9):
        errors.append(f"data.splits must sum to 1.0; got {split_total}")

    text_conditioned = any(bool(getattr(unet, "cond_on_text_encodings", False)) for unet in unets)
    has_clip = decoder.clip is not None
    has_img_embeddings = data.img_embeddings_url is not None
    has_text_embeddings = data.text_embeddings_url is not None

    if not (has_clip or has_img_embeddings):
        errors.append("decoder training needs an image embedding source: set decoder.clip or data.img_embeddings_url")
    if text_conditioned and not (has_clip or has_text_embeddings):
        errors.append("text-conditioned decoder UNets need decoder.clip or data.text_embeddings_url")
    if has_text_embeddings and not text_conditioned:
        errors.append("data.text_embeddings_url is set but no UNet has cond_on_text_encodings=true")

    metric_blocks = {
        "FID": evaluate.FID,
        "IS": evaluate.IS,
        "KID": evaluate.KID,
        "LPIPS": evaluate.LPIPS,
    }
    enabled_metrics = [name for name, value in metric_blocks.items() if value is not None]
    if enabled_metrics:
        warnings.append("decoder evaluation metrics enabled; torchmetrics image metrics may download weights: " + ", ".join(enabled_metrics))

    if has_placeholder(model_to_dict(config)):
        warnings.append("config still contains placeholder path/text markers; replace them before real training")

    summary = {
        "kind": "decoder",
        "unets": num_unets,
        "image_sizes": list(decoder.image_sizes) if decoder.image_sizes is not None else decoder.image_size,
        "text_conditioned_unets": sum(bool(getattr(unet, "cond_on_text_encodings", False)) for unet in unets),
        "has_clip": has_clip,
        "has_image_embeddings_url": has_img_embeddings,
        "has_text_embeddings_url": has_text_embeddings,
        "device": train.device,
        "epochs": train.epochs,
        "batch_size": data.batch_size,
        "resample_train": data.resample_train,
        "epoch_samples": train.epoch_samples,
        "tracker_log_type": config.tracker.log.log_type,
    }
    return errors, warnings, summary


def validate_prior(config: Any) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []

    prior = config.prior
    data = config.data
    train = config.train

    validate_common_positive("data.batch_size", data.batch_size, errors)
    validate_common_positive("data.num_data_points", data.num_data_points, errors)
    validate_common_positive("train.epochs", train.epochs, errors)
    validate_common_positive("prior.timesteps", prior.timesteps, errors)

    split_total = split_sum(data.splits)
    if split_total is not None and not math.isclose(split_total, 1.0, rel_tol=0.0, abs_tol=1e-9):
        errors.append(f"data.splits must sum to 1.0; got {split_total}")

    if prior.net.dim != prior.image_embed_dim:
        errors.append(f"prior.net.dim ({prior.net.dim}) must equal prior.image_embed_dim ({prior.image_embed_dim})")

    eval_timesteps = list(train.eval_timesteps or [])
    if eval_timesteps:
        if prior.sample_timesteps is None:
            errors.append("prior.sample_timesteps must be set when train.eval_timesteps is used by the native eval loop")
        else:
            for steps in eval_timesteps:
                if steps < prior.sample_timesteps or steps > prior.timesteps:
                    errors.append(
                        f"train.eval_timesteps value {steps} must be between prior.sample_timesteps ({prior.sample_timesteps}) and prior.timesteps ({prior.timesteps})"
                    )

    if not prior.condition_on_text_encodings:
        errors.append(
            "the bundled/native prior JSON launcher expects condition_on_text_encodings=true; use a custom direct DiffusionPriorTrainer loop for precomputed text embeddings"
        )
    if prior.condition_on_text_encodings and prior.clip is None:
        errors.append("text-conditioned prior training needs prior.clip so tokenized captions can be embedded")

    if prior.clip is not None and prior.clip.make not in {"openai", "open_clip", "x-clip", "coca"}:
        errors.append("prior.clip.make must be one of openai, open_clip, x-clip, or coca")

    if has_placeholder(model_to_dict(config)):
        warnings.append("config still contains placeholder path/text markers; replace them before real training")
    if prior.clip is not None:
        warnings.append("prior.clip may download CLIP/OpenCLIP/x-clip/CoCa weights when training starts")

    summary = {
        "kind": "prior",
        "clip_make": prior.clip.make if prior.clip is not None else None,
        "net_dim": prior.net.dim,
        "image_embed_dim": prior.image_embed_dim,
        "timesteps": prior.timesteps,
        "sample_timesteps": prior.sample_timesteps,
        "eval_timesteps": eval_timesteps,
        "condition_on_text_encodings": prior.condition_on_text_encodings,
        "epochs": train.epochs,
        "batch_size": data.batch_size,
        "num_data_points": data.num_data_points,
        "tracker_log_type": config.tracker.log.log_type,
    }
    return errors, warnings, summary


def print_list(title: str, values: Iterable[str]) -> None:
    values = list(values)
    if not values:
        return
    print(f"{title}:")
    for value in values:
        print(f"  - {value}")


def main() -> int:
    args = build_parser().parse_args()
    config_path = Path(args.config)

    try:
        raw_config = load_json(config_path)
        from pydantic import ValidationError
        from dalle2_pytorch.train_configs import TrainDecoderConfig, TrainDiffusionPriorConfig

        dist_version = metadata.version("dalle2-pytorch")
        if args.kind == "decoder":
            config = TrainDecoderConfig(**raw_config)
            errors, warnings, summary = validate_decoder(config)
        else:
            config = TrainDiffusionPriorConfig(**raw_config)
            errors, warnings, summary = validate_prior(config)
    except ConfigError as exc:
        print(f"CONFIG ERROR: {exc}", file=sys.stderr)
        return 2
    except ValidationError as exc:
        print("CONFIG ERROR: Pydantic validation failed", file=sys.stderr)
        print(exc, file=sys.stderr)
        return 2
    except Exception as exc:  # import errors and unexpected package issues should be visible and nonzero
        print(f"CONFIG ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print(f"dalle2-pytorch package version: {dist_version}")
    print(f"config path: {config_path}")
    print("summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    print_list("warnings", warnings)
    if errors:
        print_list("errors", errors)
        return 1

    print("validation: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
