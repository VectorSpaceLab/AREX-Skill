#!/usr/bin/env python3
"""Create a tiny self-contained Spleeter training fixture.

The helper writes deterministic WAV files plus train/validation CSV manifests for
2-stem or 4-stem custom training. It does not import Spleeter and does not need
the original repository checkout.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import struct
import sys
import wave
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Sequence

STEMS = {
    2: ["vocals", "accompaniment"],
    4: ["vocals", "drums", "bass", "other"],
}

BASE_FREQUENCIES = {
    "vocals": 440.0,
    "accompaniment": 220.0,
    "drums": 110.0,
    "bass": 82.0,
    "other": 330.0,
}


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def positive_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected number, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive number")
    return parsed


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a tiny deterministic WAV dataset and CSV manifests for "
            "Spleeter 2-stem or 4-stem training smoke tests."
        )
    )
    parser.add_argument(
        "--root",
        default="spleeter_training_fixture",
        help="Fixture output directory to create (default: %(default)s).",
    )
    parser.add_argument(
        "--stems",
        type=int,
        choices=sorted(STEMS),
        default=2,
        help="Stem layout to generate: 2 or 4 (default: %(default)s).",
    )
    parser.add_argument(
        "--songs-per-split",
        type=positive_int,
        default=2,
        help="Number of songs for each of train and validation splits.",
    )
    parser.add_argument(
        "--duration",
        type=positive_float,
        default=3.0,
        help="Duration in seconds for every generated WAV file.",
    )
    parser.add_argument(
        "--sample-rate",
        type=positive_int,
        default=8000,
        help="Sample rate for generated WAV files and optional config.",
    )
    parser.add_argument(
        "--channels",
        type=int,
        choices=(1, 2),
        default=2,
        help="Number of WAV channels and optional config n_channels.",
    )
    parser.add_argument(
        "--mix-name",
        default="mix",
        help="Mix stem name; default creates mix_path CSV columns.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Deterministic seed for per-song phases and amplitudes.",
    )
    parser.add_argument(
        "--write-config",
        metavar="PATH",
        help=(
            "Optional JSON config path to write. Relative CSV paths are written "
            "by default, so run Spleeter from the fixture root or choose "
            "--config-csv-paths absolute."
        ),
    )
    parser.add_argument(
        "--config-csv-paths",
        choices=("relative", "absolute"),
        default="relative",
        help="How train_csv/validation_csv are stored in the optional config.",
    )
    parser.add_argument(
        "--model-dir",
        default="model",
        help="model_dir value for the optional config (default: %(default)s).",
    )
    parser.add_argument(
        "--train-max-steps",
        type=positive_int,
        default=1,
        help="train_max_steps value for the optional smoke config.",
    )
    parser.add_argument(
        "--frame-length",
        type=positive_int,
        default=1024,
        help="frame_length value for the optional config.",
    )
    parser.add_argument(
        "--frame-step",
        type=positive_int,
        default=256,
        help="frame_step value for the optional config.",
    )
    parser.add_argument(
        "--T",
        type=positive_int,
        default=64,
        help="Spectrogram time dimension for the optional config.",
    )
    parser.add_argument(
        "--F",
        type=positive_int,
        default=128,
        help="Frequency-bin count for the optional config.",
    )
    return parser.parse_args(argv)


def check_config_dimensions(args: argparse.Namespace) -> None:
    max_f = args.frame_length // 2 + 1
    if args.F > max_f:
        raise SystemExit(
            f"--F {args.F} is incompatible with --frame-length {args.frame_length}; "
            f"F must be <= {max_f}."
        )
    available_frames = (args.duration * args.sample_rate - args.frame_length) / args.frame_step
    if available_frames < args.T:
        min_duration = (args.T * args.frame_step + args.frame_length) / args.sample_rate
        raise SystemExit(
            f"--duration {args.duration:g}s is too short for T={args.T}, "
            f"sample_rate={args.sample_rate}, frame_length={args.frame_length}, "
            f"frame_step={args.frame_step}; use at least {min_duration:.3f}s."
        )


def clamp(value: float, lo: float = -0.95, hi: float = 0.95) -> float:
    return max(lo, min(hi, value))


def make_source_function(
    instrument: str,
    song_index: int,
    split_index: int,
    sample_rate: int,
    channels: int,
    rng: random.Random,
) -> Callable[[int, int], float]:
    base = BASE_FREQUENCIES.get(instrument, 300.0)
    frequency = base + 7.5 * song_index + 3.0 * split_index
    amplitude = 0.18 + 0.04 * rng.random()
    phase = rng.random() * 2.0 * math.pi
    tremolo_rate = 1.0 + 0.2 * (song_index + split_index)

    def sample(i: int, channel: int) -> float:
        t = i / sample_rate
        stereo_scale = 1.0 if channel == 0 else 0.88 + 0.03 * ((song_index + channel) % 3)
        carrier = math.sin(2.0 * math.pi * frequency * t + phase)
        overtone = 0.35 * math.sin(2.0 * math.pi * frequency * 1.5 * t + phase / 2.0)
        envelope = 0.75 + 0.25 * math.sin(2.0 * math.pi * tremolo_rate * t)
        return clamp(amplitude * envelope * (carrier + overtone) * stereo_scale)

    return sample


def write_wav(
    path: Path,
    sample_rate: int,
    channels: int,
    duration: float,
    sample_fn: Callable[[int, int], float],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    n_frames = int(round(sample_rate * duration))
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        chunk = bytearray()
        for i in range(n_frames):
            for channel in range(channels):
                value = int(clamp(sample_fn(i, channel)) * 32767.0)
                chunk.extend(struct.pack("<h", value))
            if len(chunk) >= 65536:
                handle.writeframes(bytes(chunk))
                chunk.clear()
        if chunk:
            handle.writeframes(bytes(chunk))


def write_split(
    root: Path,
    split: str,
    split_index: int,
    instruments: List[str],
    args: argparse.Namespace,
) -> Path:
    rng = random.Random(args.seed + split_index * 1009)
    csv_path = root / split / f"{split}.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [f"{args.mix_name}_path"] + [f"{name}_path" for name in instruments] + ["duration"]

    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for song_index in range(args.songs_per_split):
            song_dir = root / split / f"song{song_index:03d}"
            source_functions: Dict[str, Callable[[int, int], float]] = {}
            row: Dict[str, str] = {"duration": f"{args.duration:.6f}"}

            for instrument in instruments:
                source_functions[instrument] = make_source_function(
                    instrument,
                    song_index=song_index,
                    split_index=split_index,
                    sample_rate=args.sample_rate,
                    channels=args.channels,
                    rng=rng,
                )
                rel_path = Path(split) / f"song{song_index:03d}" / f"{instrument}.wav"
                write_wav(root / rel_path, args.sample_rate, args.channels, args.duration, source_functions[instrument])
                row[f"{instrument}_path"] = rel_path.as_posix()

            def mix_sample(i: int, channel: int) -> float:
                value = sum(func(i, channel) for func in source_functions.values())
                return clamp(value / max(1, len(source_functions)))

            mix_rel = Path(split) / f"song{song_index:03d}" / f"{args.mix_name}.wav"
            write_wav(root / mix_rel, args.sample_rate, args.channels, args.duration, mix_sample)
            row[f"{args.mix_name}_path"] = mix_rel.as_posix()
            writer.writerow(row)

    return csv_path


def csv_value(path: Path, root: Path, mode: str) -> str:
    if mode == "absolute":
        return str(path.resolve())
    return path.relative_to(root).as_posix()


def write_config(root: Path, train_csv: Path, validation_csv: Path, instruments: List[str], args: argparse.Namespace) -> Path:
    config_path = Path(args.write_config)
    if not config_path.is_absolute():
        config_path = Path.cwd() / config_path
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config = {
        "train_csv": csv_value(train_csv, root, args.config_csv_paths),
        "validation_csv": csv_value(validation_csv, root, args.config_csv_paths),
        "model_dir": args.model_dir,
        "mix_name": args.mix_name,
        "instrument_list": instruments,
        "sample_rate": args.sample_rate,
        "frame_length": args.frame_length,
        "frame_step": args.frame_step,
        "T": args.T,
        "F": args.F,
        "n_channels": args.channels,
        "chunk_duration": args.duration,
        "n_chunks_per_song": 1,
        "separation_exponent": 2,
        "mask_extension": "zeros",
        "learning_rate": 1e-4,
        "batch_size": 1,
        "training_cache": "cache/training",
        "validation_cache": "cache/validation",
        "train_max_steps": args.train_max_steps,
        "throttle_secs": 20,
        "save_checkpoints_steps": max(1, min(10, args.train_max_steps)),
        "save_summary_steps": 1,
        "random_seed": args.seed,
        "model": {
            "type": "unet.unet",
            "params": {"conv_activation": "ELU", "deconv_activation": "ELU"},
        },
    }
    with config_path.open("w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
        handle.write("\n")
    return config_path


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    check_config_dimensions(args)

    root = Path(args.root)
    if not root.is_absolute():
        root = Path.cwd() / root
    root.mkdir(parents=True, exist_ok=True)

    instruments = STEMS[args.stems]
    train_csv = write_split(root, "train", 0, instruments, args)
    validation_csv = write_split(root, "validation", 1, instruments, args)

    config_path = None
    if args.write_config:
        config_path = write_config(root, train_csv, validation_csv, instruments, args)

    print(f"Created Spleeter training fixture: {root}")
    print(f"  stems: {args.stems} ({', '.join(instruments)})")
    print(f"  train CSV: {train_csv}")
    print(f"  validation CSV: {validation_csv}")
    if config_path:
        print(f"  smoke config: {config_path}")
        if args.config_csv_paths == "relative":
            print("  note: config CSV paths are relative to the fixture root; run training from that directory")
    print("Next: validate with validate_training_config.py before running spleeter train.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
