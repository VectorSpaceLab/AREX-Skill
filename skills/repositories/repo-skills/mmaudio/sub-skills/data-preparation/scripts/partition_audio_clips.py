#!/usr/bin/env python3
"""Partition audio files into deterministic clip metadata TSV rows.

This helper writes metadata only; it never trims or saves audio files.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable

import torchaudio

ALLOWED_SUFFIXES = {".flac", ".wav"}
HEADER = ["id", "name", "start_sample", "end_sample"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Partition audio files into clip metadata.")
    parser.add_argument("--data_dir", type=Path, required=True, help="Directory with .flac or .wav files.")
    parser.add_argument("--output_tsv", type=Path, required=True, help="Where to write the clip TSV.")
    parser.add_argument("--start", type=int, default=0, help="Start index into the sorted audio list.")
    parser.add_argument(
        "--end",
        type=int,
        default=-1,
        help="End index into the sorted audio list; use -1 to include all files.",
    )
    parser.add_argument(
        "--min_length_sec",
        type=float,
        default=8.1,
        help="Minimum clip window length in seconds.",
    )
    parser.add_argument(
        "--max_segments_per_clip",
        type=int,
        default=5,
        help="Maximum number of segments to emit per source file.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing output TSV if it already exists.",
    )
    return parser.parse_args()


def list_audio_files(data_dir: Path) -> list[Path]:
    return sorted(
        p for p in data_dir.iterdir() if p.is_file() and p.suffix.lower() in ALLOWED_SUFFIXES
    )


def read_audio_metadata(path: Path) -> tuple[int, int]:
    try:
        info = torchaudio.info(str(path))
        num_frames = int(info.num_frames)
        sample_rate = int(info.sample_rate)
    except Exception:
        waveform, sample_rate = torchaudio.load(path)
        num_frames = int(waveform.shape[1])
        sample_rate = int(sample_rate)

    if num_frames <= 0:
        raise ValueError(f"{path} has no readable frames")
    if sample_rate <= 0:
        raise ValueError(f"{path} has an invalid sample rate: {sample_rate}")
    return num_frames, sample_rate


def build_rows(
    audio_files: Iterable[Path],
    *,
    min_length_sec: float,
    max_segments_per_clip: int,
) -> list[tuple[str, str, int, int]]:
    rows: list[tuple[str, str, int, int]] = []

    for audio_path in audio_files:
        total_length, sample_rate = read_audio_metadata(audio_path)
        segment_length = int(sample_rate * min_length_sec)
        if segment_length <= 0:
            raise ValueError(f"Invalid segment length for {audio_path}: {segment_length}")
        if total_length < segment_length:
            continue

        num_segments = min(max_segments_per_clip, total_length // segment_length)
        if num_segments <= 0:
            continue

        segment_interval = 0
        if num_segments > 1:
            segment_interval = (total_length - segment_length) // (num_segments - 1)

        for segment_idx in range(num_segments):
            start_sample = segment_idx * segment_interval
            end_sample = start_sample + segment_length
            rows.append((f"{audio_path.stem}_{segment_idx}", audio_path.stem, start_sample, end_sample))

    return rows


def write_tsv(output_tsv: Path, rows: list[tuple[str, str, int, int]], *, overwrite: bool) -> None:
    if output_tsv.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {output_tsv}")

    output_tsv.parent.mkdir(parents=True, exist_ok=True)
    with output_tsv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(HEADER)
        writer.writerows(rows)


def main() -> None:
    args = parse_args()

    if not args.data_dir.exists():
        raise FileNotFoundError(f"Missing data_dir: {args.data_dir}")
    if not args.data_dir.is_dir():
        raise NotADirectoryError(f"data_dir is not a directory: {args.data_dir}")

    audio_files = list_audio_files(args.data_dir)
    if args.end == -1 or args.end > len(audio_files):
        end = len(audio_files)
    else:
        end = args.end
    if args.start < 0 or args.start > end:
        raise ValueError(f"Invalid start/end range: start={args.start}, end={end}")

    selected_files = audio_files[args.start:end]
    rows = build_rows(
        selected_files,
        min_length_sec=args.min_length_sec,
        max_segments_per_clip=args.max_segments_per_clip,
    )
    write_tsv(args.output_tsv, rows, overwrite=args.overwrite)

    print(f"Scanned {len(selected_files)} files from {args.data_dir}")
    print(f"Wrote {len(rows)} clip rows to {args.output_tsv}")


if __name__ == "__main__":
    main()
