#!/usr/bin/env python3
"""Create a tiny deterministic MUSDB-like evaluation fixture.

The generated tree is suitable for Spleeter `evaluate` layout checks:

    ROOT/test/song0/mixture.wav
    ROOT/test/song0/vocals.wav
    ROOT/test/song0/drums.wav
    ROOT/test/song0/bass.wav
    ROOT/test/song0/other.wav

It uses only the Python standard library and does not import Spleeter or require
an original source checkout. The audio is synthetic and not a meaningful model
benchmark.
"""

from __future__ import annotations

import argparse
import math
import struct
import sys
import wave
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

INSTRUMENTS: Tuple[str, ...] = ("vocals", "drums", "bass", "other")
FREQUENCIES: Dict[str, float] = {
    "vocals": 440.0,
    "drums": 110.0,
    "bass": 82.41,
    "other": 261.63,
}
AMPLITUDES: Dict[str, float] = {
    "vocals": 0.16,
    "drums": 0.14,
    "bass": 0.18,
    "other": 0.12,
}


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive number")
    return parsed


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a tiny MUSDB-like test split with mixture.wav and "
            "vocals/drums/bass/other source WAV files."
        )
    )
    parser.add_argument(
        "root",
        type=Path,
        help="Output dataset root to create or populate, for example ./tiny_musdb_eval.",
    )
    parser.add_argument(
        "--songs",
        type=positive_int,
        default=2,
        help="Number of test/songN directories to create (default: 2).",
    )
    parser.add_argument(
        "--duration",
        type=positive_float,
        default=3.0,
        help="Duration of each WAV file in seconds (default: 3.0).",
    )
    parser.add_argument(
        "--sample-rate",
        type=positive_int,
        default=44100,
        help="Sample rate for generated WAV files (default: 44100).",
    )
    parser.add_argument(
        "--channels",
        type=int,
        choices=(1, 2),
        default=2,
        help="Number of audio channels, 1 or 2 (default: 2).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace fixture WAV files if they already exist.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the success summary.",
    )
    return parser.parse_args(argv)


def target_paths(root: Path, songs: int) -> List[Path]:
    paths: List[Path] = []
    for song_index in range(songs):
        song_dir = root / "test" / f"song{song_index}"
        paths.append(song_dir / "mixture.wav")
        for instrument in INSTRUMENTS:
            paths.append(song_dir / f"{instrument}.wav")
    return paths


def ensure_safe_targets(paths: Iterable[Path], overwrite: bool) -> None:
    existing = [path for path in paths if path.exists()]
    if existing and not overwrite:
        preview = "\n".join(f"  - {path}" for path in existing[:10])
        extra = "" if len(existing) <= 10 else f"\n  ... and {len(existing) - 10} more"
        raise FileExistsError(
            "Refusing to overwrite existing fixture files without --overwrite:\n"
            f"{preview}{extra}"
        )


def source_sample(instrument: str, song_index: int, frame: int, sample_rate: int, channel: int) -> float:
    """Return one deterministic floating-point sample in [-1, 1]."""
    frequency = FREQUENCIES[instrument] * (1.0 + 0.03 * song_index)
    amplitude = AMPLITUDES[instrument]
    time = frame / sample_rate
    phase = 0.37 * song_index + 0.19 * channel
    value = amplitude * math.sin((2.0 * math.pi * frequency * time) + phase)
    if instrument == "drums":
        # Add a deterministic pulse-like modulation while staying tiny and smooth.
        value *= 0.55 + 0.45 * math.sin(2.0 * math.pi * 3.0 * time) ** 2
    return value


def render_frames(
    kind: str,
    song_index: int,
    total_frames: int,
    sample_rate: int,
    channels: int,
) -> bytes:
    frames = bytearray()
    for frame in range(total_frames):
        for channel in range(channels):
            if kind == "mixture":
                value = sum(
                    source_sample(instrument, song_index, frame, sample_rate, channel)
                    for instrument in INSTRUMENTS
                )
            else:
                value = source_sample(kind, song_index, frame, sample_rate, channel)
            value = max(-0.98, min(0.98, value))
            frames.extend(struct.pack("<h", int(round(value * 32767.0))))
    return bytes(frames)


def write_wav(path: Path, frames: bytes, sample_rate: int, channels: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(frames)


def create_fixture(args: argparse.Namespace) -> None:
    root = args.root
    if root.exists() and not root.is_dir():
        raise NotADirectoryError(f"Output root exists and is not a directory: {root}")

    paths = target_paths(root, args.songs)
    ensure_safe_targets(paths, args.overwrite)

    total_frames = int(round(args.duration * args.sample_rate))
    for song_index in range(args.songs):
        song_dir = root / "test" / f"song{song_index}"
        for kind in ("mixture", *INSTRUMENTS):
            frames = render_frames(kind, song_index, total_frames, args.sample_rate, args.channels)
            write_wav(song_dir / f"{kind}.wav", frames, args.sample_rate, args.channels)

    if not args.quiet:
        print(
            "Created MUSDB-like fixture: "
            f"{root} ({args.songs} songs, {args.duration:g}s, "
            f"{args.sample_rate} Hz, {args.channels} channel(s))"
        )
        print("Expected evaluation root argument: --mus_dir", root)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        create_fixture(args)
    except Exception as exc:  # noqa: BLE001 - concise CLI helper error path.
        print(f"create_eval_fixture.py: error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
