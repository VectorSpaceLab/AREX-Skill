#!/usr/bin/env python3
"""Validate an MMAudio feature-preparation plan and print launch commands.

This helper never runs extraction and never writes feature tensors.
"""

from __future__ import annotations

import argparse
import csv
import shlex
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

AUDIO_EXTS = {".flac", ".wav"}
VIDEO_EXTS = {".mp4"}


@dataclass(frozen=True)
class ModeSpec:
    name: str
    sample_rate: int
    audio_samples: int
    latent_seq_len: int
    latent_dim: int
    clip_seq_len: int
    sync_seq_len: int
    text_seq_len: int
    text_dim: int = 1024
    clip_dim: int = 1024
    sync_dim: int = 768


MODE_SPECS: dict[str, ModeSpec] = {
    "16k": ModeSpec(
        name="16k",
        sample_rate=16000,
        audio_samples=128000,
        latent_seq_len=250,
        latent_dim=20,
        clip_seq_len=64,
        sync_seq_len=192,
        text_seq_len=77,
    ),
    "44k": ModeSpec(
        name="44k",
        sample_rate=44100,
        audio_samples=353280,
        latent_seq_len=345,
        latent_dim=40,
        clip_seq_len=64,
        sync_seq_len=192,
        text_seq_len=77,
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an MMAudio feature-preparation plan.")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--strict", action="store_true", help="Treat duplicates as blocking errors.")

    subparsers = parser.add_subparsers(dest="kind", required=True)

    audio = subparsers.add_parser("audio", help="Validate an audio-text feature plan.", parents=[common])
    audio.add_argument("--data_dir", type=Path, required=True, help="Directory with .flac or .wav files.")
    audio.add_argument("--captions_tsv", type=Path, required=True, help="Caption TSV with id and caption columns.")
    audio.add_argument("--clips_tsv", type=Path, required=True, help="Clip TSV with id, name, start_sample, and end_sample columns.")
    audio.add_argument("--latent_dir", type=Path, required=True, help="Directory for temporary latent shard files.")
    audio.add_argument("--output_dir", type=Path, required=True, help="Final memmap output directory.")
    audio.add_argument("--mode", choices=sorted(MODE_SPECS), default="16k", help="Feature mode to validate.")
    audio.add_argument("--nproc_per_node", type=int, default=1, help="Torchrun worker count to print in the launch command.")
    audio.add_argument("--batch_size", type=int, default=32, help="Per-worker batch size to print in the launch command.")
    audio.add_argument("--num_workers", type=int, default=8, help="Per-worker dataloader worker count to print in the launch command.")

    video = subparsers.add_parser("video", help="Validate a video-text feature plan.", parents=[common])
    video.add_argument("--data_dir", type=Path, required=True, help="Directory with .mp4 files.")
    video.add_argument("--subset_tsv", type=Path, required=True, help="Subset TSV with id and label columns.")
    video.add_argument("--latent_dir", type=Path, required=True, help="Directory for temporary latent shard files.")
    video.add_argument("--output_dir", type=Path, required=True, help="Final memmap output directory.")
    video.add_argument("--split", required=True, help="Split name to validate, such as example, train, val, or test.")
    video.add_argument("--mode", choices=sorted(MODE_SPECS), default="16k", help="Feature mode to validate.")
    video.add_argument("--nproc_per_node", type=int, default=1, help="Torchrun worker count to print in the launch command.")
    video.add_argument("--batch_size", type=int, default=16, help="Reference batch size to include in the report.")
    video.add_argument("--num_workers", type=int, default=16, help="Reference dataloader worker count to include in the report.")

    return parser.parse_args()


def load_tsv_rows(path: Path, required_columns: set[str]) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing TSV: {path}")
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"TSV has no header: {path}")
        header = set(reader.fieldnames)
        missing = sorted(required_columns - header)
        if missing:
            raise ValueError(f"{path} is missing required columns: {', '.join(missing)}")
        rows = [clean_row(row) for row in reader]
    if not rows:
        raise ValueError(f"TSV is empty: {path}")
    return rows


def clean_row(row: dict[str, str | None]) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for key, value in row.items():
        if value is None:
            cleaned[key] = ""
        else:
            cleaned[key] = value.strip()
    return cleaned


def duplicate_values(values: Iterable[str]) -> list[str]:
    counts: Counter[str] = Counter()
    duplicates: list[str] = []
    for value in values:
        counts[value] += 1
        if counts[value] == 2:
            duplicates.append(value)
    return duplicates


def collect_media_stems(data_dir: Path, allowed_suffixes: set[str]) -> set[str]:
    if not data_dir.exists():
        raise FileNotFoundError(f"Missing data_dir: {data_dir}")
    if not data_dir.is_dir():
        raise NotADirectoryError(f"data_dir is not a directory: {data_dir}")
    return {
        path.stem
        for path in sorted(data_dir.iterdir())
        if path.is_file() and path.suffix.lower() in allowed_suffixes
    }


def warn(msg: str) -> None:
    print(f"WARN: {msg}", file=sys.stderr)


def build_audio_command(args: argparse.Namespace) -> list[str]:
    return [
        "torchrun",
        "--standalone",
        f"--nproc_per_node={args.nproc_per_node}",
        "training/extract_audio_training_latents.py",
        "--data_dir",
        str(args.data_dir),
        "--captions_tsv",
        str(args.captions_tsv),
        "--clips_tsv",
        str(args.clips_tsv),
        "--latent_dir",
        str(args.latent_dir),
        "--output_dir",
        str(args.output_dir),
        "--batch_size",
        str(args.batch_size),
        "--num_workers",
        str(args.num_workers),
    ]


def build_video_command(args: argparse.Namespace) -> list[str]:
    return [
        "torchrun",
        "--standalone",
        f"--nproc_per_node={args.nproc_per_node}",
        "training/extract_video_training_latents.py",
        "--latent_dir",
        str(args.latent_dir),
        "--output_dir",
        str(args.output_dir),
    ]


def report_mode(mode: str) -> ModeSpec:
    spec = MODE_SPECS[mode]
    print(f"Mode: {spec.name}")
    print(f"  sample_rate: {spec.sample_rate}")
    print(f"  audio_samples: {spec.audio_samples}")
    print(f"  latent_seq_len: {spec.latent_seq_len}")
    print(f"  latent_dim: {spec.latent_dim}")
    print(f"  clip_seq_len: {spec.clip_seq_len}")
    print(f"  sync_seq_len: {spec.sync_seq_len}")
    print(f"  text_seq_len: {spec.text_seq_len}")
    print(f"  text_dim: {spec.text_dim}")
    print(f"  clip_dim: {spec.clip_dim}")
    print(f"  sync_dim: {spec.sync_dim}")
    return spec


def report_output_paths(output_dir: Path, split: str | None = None) -> None:
    if split is None:
        base = output_dir.name
        print(f"Expected memmap dir: {output_dir}")
        print(f"Expected metadata TSV: {output_dir.parent / f'{base}.tsv'}")
    else:
        name = f"vgg-{split}"
        print(f"Expected memmap dir: {output_dir / name}")
        print(f"Expected metadata TSV: {output_dir / f'{name}.tsv'}")


def maybe_warn_existing(path: Path, label: str) -> None:
    if not path.exists():
        return
    if not path.is_dir():
        warn(f"{label} exists but is not a directory: {path}")
        return
    if any(path.iterdir()):
        warn(f"{label} already exists and is not empty: {path}")


def validate_audio(args: argparse.Namespace) -> int:
    spec = report_mode(args.mode)
    print("Plan: audio-text feature extraction")

    captions_rows = load_tsv_rows(args.captions_tsv, {"id", "caption"})
    clips_rows = load_tsv_rows(args.clips_tsv, {"id", "name", "start_sample", "end_sample"})
    audio_stems = collect_media_stems(args.data_dir, AUDIO_EXTS)

    caption_ids = [row["id"] for row in captions_rows]
    clip_names = [row["name"] for row in clips_rows]
    duplicate_caption_ids = duplicate_values(caption_ids)
    duplicate_clip_ids = duplicate_values(row["id"] for row in clips_rows)
    missing_audio = sorted({name for name in clip_names if name not in audio_stems})
    missing_captions = sorted({name for name in clip_names if name not in set(caption_ids)})

    blocking: list[str] = []
    if missing_audio:
        blocking.append(f"missing audio files for clip names: {', '.join(missing_audio[:8])}")
    if missing_captions:
        blocking.append(f"missing captions for clip names: {', '.join(missing_captions[:8])}")

    bad_ranges: list[str] = []
    for row in clips_rows:
        try:
            start = int(row["start_sample"])
            end = int(row["end_sample"])
        except ValueError:
            bad_ranges.append(row["id"])
            continue
        if start < 0 or end <= start:
            bad_ranges.append(row["id"])
    if bad_ranges:
        blocking.append(f"invalid clip ranges for ids: {', '.join(bad_ranges[:8])}")

    if duplicate_caption_ids:
        msg = f"duplicate caption ids ({len(duplicate_caption_ids)}): {', '.join(duplicate_caption_ids[:8])}"
        if args.strict:
            blocking.append(msg)
        else:
            warn(msg)
    if duplicate_clip_ids:
        msg = f"duplicate clip ids ({len(duplicate_clip_ids)}): {', '.join(duplicate_clip_ids[:8])}"
        if args.strict:
            blocking.append(msg)
        else:
            warn(msg)

    maybe_warn_existing(args.latent_dir, "latent_dir")
    maybe_warn_existing(args.output_dir, "output_dir")

    print(f"Caption rows: {len(captions_rows)}")
    print(f"Clip rows: {len(clips_rows)}")
    print(f"Available audio stems: {len(audio_stems)}")
    report_output_paths(args.output_dir)
    print("Expected tensors:")
    print(f"  mean/std: [N, {spec.latent_seq_len}, {spec.latent_dim}]")
    print(f"  text_features: [N, {spec.text_seq_len}, {spec.text_dim}]")
    print("Launch command:")
    print(shlex.join(build_audio_command(args)))
    print("Upstream extractor note: confirm the 16k or 44k mode block before launch.")

    if blocking:
        print("Blocking issues:")
        for item in blocking:
            print(f"- {item}")
        return 1
    print("Plan validation: OK")
    return 0


def validate_video(args: argparse.Namespace) -> int:
    spec = report_mode(args.mode)
    print("Plan: video-text feature extraction")

    subset_rows = load_tsv_rows(args.subset_tsv, {"id", "label"})
    video_stems = collect_media_stems(args.data_dir, VIDEO_EXTS)

    subset_ids = [row["id"] for row in subset_rows]
    duplicate_subset_ids = duplicate_values(subset_ids)
    missing_videos = sorted({video_id for video_id in subset_ids if video_id not in video_stems})

    blocking: list[str] = []
    if missing_videos:
        blocking.append(f"missing videos for ids: {', '.join(missing_videos[:8])}")

    if duplicate_subset_ids:
        msg = f"duplicate subset ids ({len(duplicate_subset_ids)}): {', '.join(duplicate_subset_ids[:8])}"
        if args.strict:
            blocking.append(msg)
        else:
            warn(msg)

    maybe_warn_existing(args.latent_dir, "latent_dir")
    maybe_warn_existing(args.output_dir, "output_dir")

    print(f"Subset rows: {len(subset_rows)}")
    print(f"Available video stems: {len(video_stems)}")
    print(f"Split: {args.split}")
    print(f"Reference loader hints: batch_size={args.batch_size}, num_workers={args.num_workers}")
    report_output_paths(args.output_dir, split=args.split)
    print("Expected tensors:")
    print(f"  mean/std: [N, {spec.latent_seq_len}, {spec.latent_dim}]")
    print(f"  clip_features: [N, {spec.clip_seq_len}, {spec.clip_dim}]")
    print(f"  sync_features: [N, {spec.sync_seq_len}, {spec.sync_dim}]")
    print(f"  text_features: [N, {spec.text_seq_len}, {spec.text_dim}]")
    print("Launch command:")
    print(shlex.join(build_video_command(args)))
    print("Upstream extractor note: confirm the split entry and the 16k or 44k mode block before launch.")

    if blocking:
        print("Blocking issues:")
        for item in blocking:
            print(f"- {item}")
        return 1
    print("Plan validation: OK")
    return 0


def main() -> None:
    args = parse_args()
    if args.kind == "audio":
        raise SystemExit(validate_audio(args))
    if args.kind == "video":
        raise SystemExit(validate_video(args))
    raise SystemExit("Unknown plan kind")


if __name__ == "__main__":
    main()
