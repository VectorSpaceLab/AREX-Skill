#!/usr/bin/env python3
"""Report OpenCLIP training parser defaults and selected options without training.

Usage:
    python sub-skills/training/scripts/training_arg_report.py -- --dataset-type csv --train-data DATA/train.tsv

The optional `--` separates this helper's flags from the OpenCLIP training flags.
This script imports `open_clip_train.params.parse_args` only; it does not create
models, tokenizers, data loaders, distributed process groups, or checkpoints.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


DEFAULT_KEYS = [
    "model",
    "dataset_type",
    "train_data",
    "val_data",
    "train_num_samples",
    "val_num_samples",
    "csv_separator",
    "csv_img_key",
    "csv_caption_key",
    "text_key",
    "json_text_key",
    "workers",
    "batch_size",
    "epochs",
    "warmup",
    "lr",
    "beta1",
    "beta2",
    "eps",
    "wd",
    "opt",
    "lr_scheduler",
    "precision",
    "device",
    "report_to",
    "accum_freq",
    "torchcompile",
    "torchcompile_strategy",
    "torchcompile_backend",
    "torchcompile_mode",
    "grad_checkpointing",
    "fsdp",
    "fsdp_checkpoint",
    "save_frequency",
    "save_most_recent",
    "resume",
    "remote_sync",
    "remote_sync_protocol",
    "dataset_resampled",
    "train_data_upsampling_factors",
    "audio_ext",
    "audio_fill",
    "audio_trunc",
    "audio_multiprocessing_context",
    "use_naflex",
    "force_naflex_vision",
    "naflex_num_train_image_tokens",
    "naflex_seq_lens",
    "naflex_max_tokens_per_batch",
    "naflex_pad_multiple",
    "text_pad_multiple",
    "length_bucketing",
    "genlip",
    "genlap",
    "naflexclap",
    "siglip",
    "distill_model",
    "distill_pretrained",
    "local_loss",
    "gather_with_grad",
]

FAMILIES = {
    "data": [
        "dataset_type", "train_data", "val_data", "train_num_samples", "val_num_samples",
        "dataset_resampled", "train_data_upsampling_factors", "csv_separator", "csv_img_key",
        "csv_caption_key", "text_key", "json_text_key", "workers", "batch_size",
    ],
    "task_loss": [
        "model", "siglip", "distill", "distill_model", "distill_pretrained", "local_loss",
        "gather_with_grad", "loss_dist_impl", "coca_caption_loss_weight", "coca_contrastive_loss_weight",
        "genlip", "genlap", "naflexclap", "use_naflex", "force_naflex_vision",
    ],
    "optim_scheduler": [
        "opt", "opt_kwargs", "opt_fallback_list", "lr", "beta1", "beta2", "eps", "momentum",
        "wd", "wd_exclude_patterns", "text_layer_decay", "image_layer_decay", "audio_layer_decay",
        "warmup", "skip_scheduler", "lr_scheduler", "epochs", "epochs_cooldown",
    ],
    "precision_compile_distributed": [
        "precision", "device", "accum_freq", "grad_checkpointing", "torchcompile",
        "torchcompile_strategy", "torchcompile_backend", "torchcompile_mode", "distributed", "world_size",
        "fsdp", "fsdp_checkpoint", "ddp_static_graph", "use_bn_sync",
    ],
    "checkpoint_logging": [
        "logs", "name", "save_frequency", "save_most_recent", "delete_previous_checkpoint",
        "resume", "report_to", "log_every_n_steps", "log_metric_every_n_steps", "train_loss_ema_samples",
        "remote_sync", "remote_sync_frequency", "remote_sync_protocol",
    ],
    "audio": [
        "dataset_type", "audio_ext", "audio_fill", "audio_trunc", "audio_fusion", "audio_int16_normalize",
        "audio_multiprocessing_context", "audio_zeroshot_dataset", "audio_zeroshot_split",
    ],
    "naflex": [
        "use_naflex", "force_naflex_vision", "naflex_num_train_image_tokens", "naflex_patch_sizes",
        "naflex_seq_lens", "naflex_max_tokens_per_batch", "naflex_max_text_tokens", "naflex_batch_divisor",
        "naflex_loss_scale", "naflex_pad_multiple", "text_pad_multiple", "length_bucketing", "bucket_pool",
        "bucket_chunk",
    ],
}


def _jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(val) for key, val in value.items()}
    return repr(value)


def parse_helper_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    parser.add_argument(
        "--family",
        choices=tuple(FAMILIES),
        action="append",
        help="Limit output to one or more option families.",
    )
    parser.add_argument(
        "training_args",
        nargs=argparse.REMAINDER,
        help="OpenCLIP training args. Prefix with -- when passing options.",
    )
    args = parser.parse_args(argv)
    if args.training_args and args.training_args[0] == "--":
        args.training_args = args.training_args[1:]
    return args


def main(argv: list[str]) -> int:
    helper_args = parse_helper_args(argv)
    try:
        from open_clip_train.params import parse_args as parse_training_args
    except Exception as exc:  # pragma: no cover - environment-specific import failure
        print("ERROR: could not import open_clip_train.params.parse_args.", file=sys.stderr)
        print("Install OpenCLIP with training support or run in an environment where open_clip_train is importable.", file=sys.stderr)
        print(f"Import error: {exc}", file=sys.stderr)
        return 2

    try:
        parsed = parse_training_args(helper_args.training_args)
    except SystemExit as exc:
        return int(exc.code or 0)
    except Exception as exc:
        print(f"ERROR: OpenCLIP parse_args rejected the provided arguments: {exc}", file=sys.stderr)
        return 2

    selected_keys: list[str]
    if helper_args.family:
        selected_keys = []
        for family in helper_args.family:
            selected_keys.extend(FAMILIES[family])
    else:
        selected_keys = DEFAULT_KEYS

    report = {
        key: _jsonable(getattr(parsed, key))
        for key in dict.fromkeys(selected_keys)
        if hasattr(parsed, key)
    }

    if helper_args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    print("OpenCLIP training argument report")
    print(f"  parsed training args: {len(helper_args.training_args)} token(s)")
    if helper_args.family:
        print("  families: " + ", ".join(helper_args.family))
    print("")
    for key in report:
        print(f"{key}: {report[key]!r}")

    print("\nNotes:")
    print("- This report only runs open_clip_train.params.parse_args; it does not train or build data loaders.")
    print("- Defaults are parser defaults after model-name side effects such as genlip/genlap/naflexclap detection.")
    print("- Use --format json for machine-readable inspection.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
