#!/usr/bin/env python3
"""Safely plan or run Coqui TTS speaker embedding computation for a dataset."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple
from urllib.parse import urlparse


def _is_url(value: str | None) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"}


def _path_exists_or_url(value: str, allow_network: bool, label: str) -> Tuple[bool, str | None]:
    if _is_url(value):
        if allow_network:
            return True, None
        return False, f"{label} is a URL; pass --allow-network only after accepting download/cache behavior"
    path = Path(os.path.expanduser(value))
    if not path.exists():
        return False, f"{label} does not exist: {path}"
    return True, None


def _dataset_args_valid(args: argparse.Namespace) -> Tuple[bool, str | None]:
    if args.config_dataset_path:
        path = Path(os.path.expanduser(args.config_dataset_path))
        if not path.is_file():
            return False, f"dataset config does not exist: {path}"
        return True, None
    missing = [
        name
        for name in ("formatter_name", "dataset_name", "dataset_path")
        if not getattr(args, name)
    ]
    if missing:
        return False, "provide --config-dataset-path or all of --formatter-name, --dataset-name, and --dataset-path"
    dataset_root = Path(os.path.expanduser(args.dataset_path))
    if not dataset_root.is_dir():
        return False, f"dataset path does not exist or is not a directory: {dataset_root}"
    return True, None


def _load_sample_count(args: argparse.Namespace) -> Dict[str, Any]:
    from TTS.config import load_config
    from TTS.config.shared_configs import BaseDatasetConfig
    from TTS.tts.datasets import load_tts_samples

    if args.config_dataset_path:
        c_dataset = load_config(args.config_dataset_path)
        train, eval_items = load_tts_samples(c_dataset.datasets, eval_split=not args.no_eval)
    else:
        c_dataset = BaseDatasetConfig(
            formatter=args.formatter_name,
            dataset_name=args.dataset_name,
            path=args.dataset_path,
            meta_file_train=args.meta_file_train or "",
            meta_file_val=args.meta_file_val or "",
        )
        train, eval_items = load_tts_samples(c_dataset, eval_split=not args.no_eval)
    return {"train": len(train), "eval": None if eval_items is None else len(eval_items)}


def _run_compute(args: argparse.Namespace) -> None:
    from TTS.bin.compute_embeddings import compute_embeddings

    compute_embeddings(
        args.encoder_model_path,
        args.encoder_config_path,
        args.output_path,
        old_speakers_file=args.old_file,
        old_append=args.old_append,
        config_dataset_path=args.config_dataset_path,
        formatter_name=args.formatter_name,
        dataset_name=args.dataset_name,
        dataset_path=args.dataset_path,
        meta_file_train=args.meta_file_train,
        meta_file_val=args.meta_file_val,
        disable_cuda=(args.device == "cpu"),
        no_eval=args.no_eval,
    )


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--encoder-model-path", required=True, help="Explicit speaker encoder checkpoint path or URL. No network default is assumed.")
    parser.add_argument("--encoder-config-path", required=True, help="Explicit speaker encoder config path or URL. No network default is assumed.")
    parser.add_argument("--config-dataset-path", default=None, help="Config containing dataset definitions. Alternative to formatter/dataset arguments.")
    parser.add_argument("--formatter-name", default=None, help="Dataset formatter name when not using --config-dataset-path.")
    parser.add_argument("--dataset-name", default=None, help="Dataset name used in audio_unique_name keys when not using --config-dataset-path.")
    parser.add_argument("--dataset-path", default=None, help="Dataset root when not using --config-dataset-path.")
    parser.add_argument("--meta-file-train", default=None, help="Train metadata file for formatter mode.")
    parser.add_argument("--meta-file-val", default=None, help="Validation metadata file for formatter mode.")
    parser.add_argument("--output-path", default=None, help="Output .pth path or directory. Required with --run.")
    parser.add_argument("--old-file", default=None, help="Existing speaker embedding file to reuse/append.")
    parser.add_argument("--old-append", action="store_true", help="Append new embeddings to --old-file instead of replacing mapping.")
    parser.add_argument("--device", choices=["cpu", "auto"], default="cpu", help="cpu is safest default; auto allows CUDA when available.")
    parser.add_argument("--no-eval", action="store_true", help="Do not include eval samples.")
    parser.add_argument("--allow-network", action="store_true", help="Allow URL encoder paths that may download/cache files.")
    parser.add_argument("--skip-sample-load", action="store_true", help="Dry-run argument validation without loading dataset samples.")
    parser.add_argument("--run", action="store_true", help="Actually compute embeddings. Omit for dry-run planning only.")
    parser.add_argument("--json", action="store_true", help="Emit dry-run plan as JSON.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    errors = []
    warnings = []

    for label, value in (("encoder model", args.encoder_model_path), ("encoder config", args.encoder_config_path)):
        ok, msg = _path_exists_or_url(value, args.allow_network, label)
        if not ok and msg:
            errors.append(msg)
    ok, msg = _dataset_args_valid(args)
    if not ok and msg:
        errors.append(msg)
    if args.old_file:
        old_path = Path(os.path.expanduser(args.old_file))
        if not old_path.exists():
            errors.append(f"old speaker file does not exist: {old_path}")
    if args.old_append and not args.old_file:
        errors.append("--old-append requires --old-file")
    if args.run and not args.output_path:
        errors.append("--output-path is required with --run")
    if args.device == "auto":
        warnings.append("device=auto may use CUDA if available; ensure GPU memory is acceptable")
    if _is_url(args.encoder_model_path) or _is_url(args.encoder_config_path):
        warnings.append("URL encoder paths can download files and use cache/disk/network; prefer explicit local paths for reproducible runs")

    plan: Dict[str, Any] = {
        "run": args.run,
        "device": args.device,
        "allow_network": args.allow_network,
        "dataset_mode": "config" if args.config_dataset_path else "formatter_args",
        "errors": errors,
        "warnings": warnings,
    }

    if not errors and not args.skip_sample_load:
        try:
            plan["sample_counts"] = _load_sample_count(args)
        except Exception as exc:
            errors.append(f"dataset sample load failed: {type(exc).__name__}: {exc}")

    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True, default=str))
    else:
        print("Coqui TTS speaker embedding plan")
        print(f"mode: {'RUN' if args.run else 'DRY-RUN'}")
        print(f"device: {args.device}")
        print(f"network allowed: {args.allow_network}")
        if "sample_counts" in plan:
            counts = plan["sample_counts"]
            print(f"samples: train={counts['train']} eval={counts['eval']}")
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"  - {warning}")
        if errors:
            print("\nErrors:")
            for error in errors:
                print(f"  - {error}")
        if not errors and not args.run:
            print("\nDry-run OK. Re-run with --run and --output-path to compute embeddings.")

    if errors:
        return 2
    if not args.run:
        return 0

    try:
        _run_compute(args)
    except Exception as exc:
        print(f"Embedding computation failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
