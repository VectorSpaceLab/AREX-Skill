#!/usr/bin/env python3
"""Create tiny wav and mel fixtures for HiFi-GAN inference smoke tests.

The helper writes a mono PCM16 wav file under `test_files/` and a mel `.npy`
file under `test_mel_files/`. The mel helper can optionally emit a wrong-rank
array for negative testing.
"""

from __future__ import annotations

import argparse
import math
import wave
from pathlib import Path

import numpy as np


def write_wav(path: Path, sample_rate: int, duration_s: float, frequency_hz: float, amplitude: float) -> None:
    sample_count = max(1, int(round(sample_rate * duration_s)))
    time = np.arange(sample_count, dtype=np.float32) / float(sample_rate)
    waveform = amplitude * np.sin(2.0 * math.pi * frequency_hz * time)
    pcm = np.clip(waveform, -1.0, 0.9999695)
    pcm = (pcm * 32767.0).astype(np.int16)

    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())


def make_mel_array(seed: int, mel_bins: int, mel_frames: int, mel_rank: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    base = np.linspace(-1.0, 1.0, mel_bins * mel_frames, dtype=np.float32).reshape(mel_bins, mel_frames)
    noise = 0.05 * rng.standard_normal(base.shape).astype(np.float32)
    mel = base + noise

    if mel_rank == 1:
        return mel[:, 0].astype(np.float32)
    if mel_rank == 2:
        return mel.astype(np.float32)
    if mel_rank == 3:
        return mel[np.newaxis, :, :].astype(np.float32)
    raise ValueError(f"Unsupported mel rank: {mel_rank}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a tiny wav file and mel npy file for HiFi-GAN smoke tests."
    )
    parser.add_argument("--output-root", required=True, type=Path, help="Root directory to write the fixture tree into.")
    parser.add_argument("--stem", default="sample", help="Base filename stem for the generated wav and mel files.")
    parser.add_argument("--sample-rate", type=int, default=22050, help="Sample rate to encode into the wav fixture.")
    parser.add_argument("--wav-duration", type=float, default=0.05, help="Duration of the synthetic wav in seconds.")
    parser.add_argument("--wav-frequency", type=float, default=440.0, help="Sine-wave frequency for the wav fixture.")
    parser.add_argument("--wav-amplitude", type=float, default=0.2, help="Amplitude for the synthetic wav fixture.")
    parser.add_argument("--mel-bins", type=int, default=80, help="Number of mel bins to write into the npy fixture.")
    parser.add_argument("--mel-frames", type=int, default=8, help="Number of mel frames to write into the npy fixture.")
    parser.add_argument(
        "--mel-rank",
        type=int,
        default=2,
        choices=(1, 2, 3),
        help="Rank of the mel array. Use 2 for the standard single-sample layout, 3 to include a batch axis, or 1 for a negative test.",
    )
    parser.add_argument("--seed", type=int, default=1234, help="Random seed for the mel fixture noise.")
    args = parser.parse_args()

    test_files_dir = args.output_root / "test_files"
    test_mel_dir = args.output_root / "test_mel_files"
    test_files_dir.mkdir(parents=True, exist_ok=True)
    test_mel_dir.mkdir(parents=True, exist_ok=True)

    wav_path = test_files_dir / f"{args.stem}.wav"
    mel_path = test_mel_dir / f"{args.stem}.npy"

    write_wav(wav_path, args.sample_rate, args.wav_duration, args.wav_frequency, args.wav_amplitude)
    mel = make_mel_array(args.seed, args.mel_bins, args.mel_frames, args.mel_rank)
    np.save(mel_path, mel.astype(np.float32))

    print(f"Wrote wav fixture: {wav_path.relative_to(args.output_root)}")
    print(f"Wrote mel fixture: {mel_path.relative_to(args.output_root)}")
    print(f"Mel shape: {tuple(mel.shape)}")


if __name__ == "__main__":
    main()
