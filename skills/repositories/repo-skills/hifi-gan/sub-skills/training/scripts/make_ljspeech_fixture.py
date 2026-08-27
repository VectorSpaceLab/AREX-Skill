#!/usr/bin/env python3
"""Create a tiny LJSpeech-style fixture for HiFi-GAN training checks.

The fixture mirrors the parts of LJSpeech that train.py actually consumes:
`wavs/`, `training.txt`, `validation.txt`, and optionally basename-matched
mel `.npy` files for fine-tuning. It generates synthetic tones only; do not use
these files for quality training.

Examples:
    python make_ljspeech_fixture.py --out-dir ./scratch/hifigan_fixture
    python make_ljspeech_fixture.py --out-dir ./scratch/hifigan_ft --with-mels
    python make_ljspeech_fixture.py --out-dir ./scratch/hifigan_bad --include-missing-wav-row
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy.io import wavfile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a tiny LJSpeech-style HiFi-GAN fixture.")
    parser.add_argument("--out-dir", default="tiny_ljspeech_fixture", help="Directory to create.")
    parser.add_argument("--train-count", type=int, default=2, help="Number of valid training wav rows to create.")
    parser.add_argument("--val-count", type=int, default=1, help="Number of valid validation wav rows to create.")
    parser.add_argument("--sample-rate", type=int, default=22050, help="Wav sample rate to write.")
    parser.add_argument("--duration-sec", type=float, default=0.25, help="Approximate duration per wav.")
    parser.add_argument("--seed", type=int, default=1234, help="Seed for deterministic mels/noise.")
    parser.add_argument("--with-mels", action="store_true", help="Also create basename-matched mel .npy files.")
    parser.add_argument("--mels-dir-name", default="ft_dataset", help="Directory name for generated mel .npy files.")
    parser.add_argument("--num-mels", type=int, default=80, help="Mel channel count for generated .npy files.")
    parser.add_argument("--hop-size", type=int, default=64, help="Hop size used to choose mel frame count.")
    parser.add_argument(
        "--include-missing-wav-row",
        action="store_true",
        help="Append a training filelist row whose wav is intentionally absent.",
    )
    parser.add_argument(
        "--include-bad-mel-name",
        action="store_true",
        help="With --with-mels, intentionally misname one mel file and omit the matching basename.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Delete an existing out-dir before writing.")
    return parser.parse_args()


def ensure_clean_dir(path: Path, overwrite: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not overwrite:
            raise SystemExit(f"Refusing to overwrite non-empty directory: {path}")
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def make_ids(prefix: str, start: int, count: int) -> list[str]:
    return [f"{prefix}{i:04d}" for i in range(start, start + count)]


def synth_tone(sample_rate: int, sample_count: int, index: int, rng: np.random.Generator) -> np.ndarray:
    t = np.arange(sample_count, dtype=np.float32) / float(sample_rate)
    base_freq = 180.0 + 35.0 * index
    audio = 0.12 * np.sin(2.0 * np.pi * base_freq * t)
    audio += 0.04 * np.sin(2.0 * np.pi * (base_freq * 1.7) * t)
    audio += 0.005 * rng.standard_normal(sample_count).astype(np.float32)
    fade = min(sample_count // 8, max(1, sample_rate // 200))
    envelope = np.ones(sample_count, dtype=np.float32)
    ramp = np.linspace(0.0, 1.0, fade, dtype=np.float32)
    envelope[:fade] = ramp
    envelope[-fade:] = ramp[::-1]
    audio = np.clip(audio * envelope, -0.95, 0.95)
    return (audio * np.iinfo(np.int16).max).astype(np.int16)


def write_filelist(path: Path, ids: Iterable[str]) -> None:
    lines = [f"{utt_id}|Synthetic fixture utterance {idx}|Synthetic fixture utterance {idx}" for idx, utt_id in enumerate(ids, 1)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_mel(num_mels: int, frames: int, index: int, rng: np.random.Generator) -> np.ndarray:
    # The values only need to have a plausible log-mel scale for wiring checks.
    time = np.linspace(0.0, 1.0, frames, dtype=np.float32)[None, :]
    channels = np.linspace(0.0, 1.0, num_mels, dtype=np.float32)[:, None]
    pattern = -5.0 + 2.0 * np.sin(2.0 * np.pi * (channels + 0.1 * index) * (time + 0.05))
    noise = 0.01 * rng.standard_normal((num_mels, frames)).astype(np.float32)
    return (pattern + noise).astype(np.float32)


def main() -> int:
    args = parse_args()
    if args.train_count < 1:
        raise SystemExit("--train-count must be at least 1")
    if args.val_count < 1:
        raise SystemExit("--val-count must be at least 1")
    if args.sample_rate <= 0 or args.duration_sec <= 0:
        raise SystemExit("--sample-rate and --duration-sec must be positive")
    if args.hop_size <= 0:
        raise SystemExit("--hop-size must be positive")

    out_dir = Path(args.out_dir).expanduser().resolve()
    ensure_clean_dir(out_dir, args.overwrite)

    wavs_dir = out_dir / "wavs"
    wavs_dir.mkdir(parents=True, exist_ok=True)

    train_ids = make_ids("LJ001-", 1, args.train_count)
    val_ids = make_ids("LJ001-", 1001, args.val_count)
    all_valid_ids = train_ids + val_ids

    sample_count = int(math.ceil(args.sample_rate * args.duration_sec / args.hop_size) * args.hop_size)
    sample_count = max(sample_count, args.hop_size)

    rng = np.random.default_rng(args.seed)
    wav_paths: list[str] = []
    for idx, utt_id in enumerate(all_valid_ids, 1):
        wav_path = wavs_dir / f"{utt_id}.wav"
        wavfile.write(wav_path, args.sample_rate, synth_tone(args.sample_rate, sample_count, idx, rng))
        wav_paths.append(str(wav_path))

    training_rows = list(train_ids)
    missing_id = None
    if args.include_missing_wav_row:
        missing_id = "LJ999-9999"
        training_rows.append(missing_id)

    training_file = out_dir / "training.txt"
    validation_file = out_dir / "validation.txt"
    write_filelist(training_file, training_rows)
    write_filelist(validation_file, val_ids)

    mels_dir = None
    bad_mel_expected = None
    bad_mel_written = None
    if args.with_mels:
        mels_dir = out_dir / args.mels_dir_name
        mels_dir.mkdir(parents=True, exist_ok=True)
        frames = max(2, sample_count // args.hop_size)
        bad_target = train_ids[min(1, len(train_ids) - 1)] if args.include_bad_mel_name else None
        for idx, utt_id in enumerate(all_valid_ids, 1):
            mel = make_mel(args.num_mels, frames, idx, rng)
            if utt_id == bad_target:
                bad_mel_expected = str(mels_dir / f"{utt_id}.npy")
                bad_mel_written = str(mels_dir / f"BADNAME-{utt_id}.npy")
                np.save(bad_mel_written, mel)
            else:
                np.save(mels_dir / f"{utt_id}.npy", mel)

    manifest = {
        "fixture_dir": str(out_dir),
        "wavs_dir": str(wavs_dir),
        "training_file": str(training_file),
        "validation_file": str(validation_file),
        "mels_dir": str(mels_dir) if mels_dir else None,
        "sample_rate": args.sample_rate,
        "sample_count": sample_count,
        "duration_sec_actual": sample_count / float(args.sample_rate),
        "train_ids": train_ids,
        "validation_ids": val_ids,
        "missing_wav_id": missing_id,
        "bad_mel_expected_path": bad_mel_expected,
        "bad_mel_written_path": bad_mel_written,
        "wav_paths": wav_paths,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
