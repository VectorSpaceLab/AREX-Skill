#!/usr/bin/env python3
"""No-network-by-default DeepFilterNet Python enhancement helper.

This script adapts the package's minimal external-usage flow into a safer
runtime helper: it requires explicit input/output files, avoids downloads unless
--allow-download is supplied, and can force CPU/CUDA selection before model
initialization.
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path
from typing import Any, Optional


def _parse_epoch(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"best", "latest", "none"}:
        return None if lowered == "none" else lowered
    try:
        return int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("epoch must be 'best', 'latest', 'none', or an integer") from exc


def _import_runtime_modules():
    missing = []
    for module in ("torch", "torchaudio", "df", "libdf"):
        try:
            importlib.import_module(module)
        except ModuleNotFoundError as exc:
            missing.append(f"{module}: {exc}")
    if missing:
        raise SystemExit(
            "Missing required DeepFilterNet runtime modules:\n"
            + "\n".join(f"  - {m}" for m in missing)
            + "\nInstall DeepFilterNet with torch, torchaudio, and deepfilterlib before retrying."
        )
    enhance_mod = importlib.import_module("df.enhance")
    io_mod = importlib.import_module("df.io")
    utils_mod = importlib.import_module("df.utils")
    torch_mod = importlib.import_module("torch")
    return enhance_mod, io_mod, utils_mod, torch_mod


def _looks_like_model_dir(path: Path) -> bool:
    return path.is_dir() and (path / "config.ini").is_file() and (path / "checkpoints").is_dir()


def _describe_model_dir_problem(path: Path) -> str:
    missing = []
    if not path.is_dir():
        missing.append("directory")
    if not (path / "config.ini").is_file():
        missing.append("config.ini")
    if not (path / "checkpoints").is_dir():
        missing.append("checkpoints/")
    return ", ".join(missing) if missing else "unknown model directory problem"


def _resolve_model_base_dir(
    requested: Optional[str], allow_download: bool, enhance_mod, utils_mod
) -> Optional[str]:
    names = set(getattr(enhance_mod, "PRETRAINED_MODELS", ()))
    default_model = getattr(enhance_mod, "DEFAULT_MODEL", "DeepFilterNet3")
    requested_or_default = requested or default_model
    bare_name = requested_or_default.removesuffix(".zip")

    if bare_name in names:
        if allow_download:
            return requested_or_default
        cache_candidate = Path(utils_mod.get_cache_dir()).expanduser() / bare_name
        if _looks_like_model_dir(cache_candidate):
            return str(cache_candidate)
        raise SystemExit(
            f"Pretrained model {bare_name!r} is not available as a verified local cache entry.\n"
            "This helper is no-network by default. Pass --model-base-dir with a local model "
            "directory containing config.ini and checkpoints/, or add --allow-download when "
            "network access is intentional."
        )

    path = Path(requested_or_default).expanduser()
    if not _looks_like_model_dir(path):
        raise SystemExit(
            f"Model directory {path!s} is not usable: missing {_describe_model_dir_problem(path)}.\n"
            "Use an extracted DeepFilterNet model directory with config.ini and checkpoints/."
        )
    return str(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Enhance one audio file with DeepFilterNet using the installed Python package. "
            "Downloads are disabled unless --allow-download is supplied."
        )
    )
    parser.add_argument("--input-file", required=True, help="Input noisy audio file.")
    parser.add_argument("--output-file", required=True, help="Output enhanced audio file.")
    parser.add_argument(
        "--model-base-dir",
        "-m",
        default=None,
        help=(
            "Local model directory containing config.ini and checkpoints/, or a pretrained "
            "name (DeepFilterNet, DeepFilterNet2, DeepFilterNet3) if cached or --allow-download is used."
        ),
    )
    parser.add_argument(
        "--allow-download",
        action="store_true",
        help="Permit package model download when a pretrained model name is not cached.",
    )
    parser.add_argument(
        "--post-filter",
        "--pf",
        dest="post_filter",
        action="store_true",
        help="Enable DeepFilterNet post-filtering for extra suppression in very noisy sections.",
    )
    parser.add_argument(
        "--atten-lim",
        type=float,
        default=None,
        help="Optional attenuation limit in dB, e.g. 12 to retain more residual noise.",
    )
    parser.add_argument(
        "--no-delay-compensation",
        dest="compensate_delay",
        action="store_false",
        default=True,
        help="Disable STFT/model delay compensation. Default keeps output aligned to input length.",
    )
    parser.add_argument(
        "--keep-model-sr",
        action="store_true",
        help="Save at the model sample rate instead of resampling back to the input sample rate.",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Set DeepFilterNet DEVICE before init_df, e.g. 'cpu' or 'cuda:0'.",
    )
    parser.add_argument(
        "--epoch",
        default="best",
        type=_parse_epoch,
        help="Checkpoint epoch: best, latest, none, or an integer. Default: best.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="DeepFilterNet logger verbosity. Default: INFO.",
    )
    parser.add_argument(
        "--dtype",
        choices=("int16", "float32"),
        default="int16",
        help="Output dtype passed to df.io.save_audio. Default: int16.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting an existing output file.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    input_path = Path(args.input_file).expanduser()
    output_path = Path(args.output_file).expanduser()
    if not input_path.is_file():
        raise SystemExit(f"Input file not found: {input_path}")
    if output_path.exists() and not args.overwrite:
        raise SystemExit(f"Output file already exists: {output_path} (pass --overwrite to replace it)")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.device:
        os.environ["DEVICE"] = args.device

    enhance_mod, io_mod, utils_mod, torch_mod = _import_runtime_modules()
    model_base_dir = _resolve_model_base_dir(
        args.model_base_dir, args.allow_download, enhance_mod, utils_mod
    )

    model, df_state, suffix, epoch = enhance_mod.init_df(
        model_base_dir=model_base_dir,
        post_filter=args.post_filter,
        log_level=args.log_level,
        log_file=None,
        epoch=args.epoch,
    )

    model_sr = int(df_state.sr())
    audio, meta = io_mod.load_audio(str(input_path), sr=model_sr)
    input_sr = int(getattr(meta, "sample_rate", model_sr))

    enhanced = enhance_mod.enhance(
        model,
        df_state,
        audio,
        pad=args.compensate_delay,
        atten_lim_db=args.atten_lim,
    )

    output_sr = model_sr
    if not args.keep_model_sr and input_sr != model_sr:
        enhanced = io_mod.resample(enhanced, model_sr, input_sr)
        output_sr = input_sr

    dtype = torch_mod.float32 if args.dtype == "float32" else torch_mod.int16
    io_mod.save_audio(str(output_path), enhanced, sr=output_sr, dtype=dtype)

    duration = enhanced.shape[-1] / float(output_sr) if output_sr else 0.0
    print("DeepFilterNet enhancement complete")
    print(f"  input:      {input_path}")
    print(f"  output:     {output_path}")
    print(f"  model_sr:   {model_sr}")
    print(f"  input_sr:   {input_sr}")
    print(f"  output_sr:  {output_sr}")
    print(f"  channels:   {enhanced.shape[0]}")
    print(f"  seconds:    {duration:.3f}")
    print(f"  suffix:     {suffix}")
    print(f"  epoch:      {epoch}")
    print(f"  device_env: {os.environ.get('DEVICE', '<package default>')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
