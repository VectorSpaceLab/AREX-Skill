#!/usr/bin/env python3
"""Validate DALLE2-pytorch decoder WebDataset and sidecar embedding layout.

Default mode checks expected filenames and shard-sidecar alignment without
loading tar payloads or large `.npy` arrays. Add `--inspect-tar` to inspect one
small tar member list and sample-key suffixes.
"""

from __future__ import annotations

import argparse
import re
import sys
import tarfile
from pathlib import Path


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def warn(message: str) -> None:
    print(f"WARNING: {message}")


def format_shard(pattern: str, shard: int, width: int) -> Path:
    return Path(pattern.format(str(shard).zfill(width)))


def sidecar_files(folder: Path) -> dict[int, Path]:
    if not folder.exists():
        fail(f"sidecar embedding folder does not exist: {folder}")
    files = sorted(folder.glob("*.npy"))
    if not files:
        fail(f"no .npy sidecar embedding files found in {folder}")
    out: dict[int, Path] = {}
    for path in files:
        match = re.search(r"_([0-9]+)\.npy$", path.name)
        if not match:
            warn(f"ignoring sidecar file without trailing _<shard>.npy pattern: {path.name}")
            continue
        out[int(match.group(1))] = path
    if not out:
        fail(f"no sidecar files in {folder} matched *_<shard>.npy")
    return out


def inspect_tar(path: Path, index_width: int, max_members: int) -> None:
    if not path.exists():
        fail(f"cannot inspect missing tar: {path}")
    try:
        with tarfile.open(path, "r") as tf:
            members = [m for m in tf.getmembers() if m.isfile()]
    except tarfile.TarError as exc:
        fail(f"could not read tar {path}: {exc}")

    print(f"INSPECT_TAR={path}")
    print(f"member_count={len(members)}")
    suffix_counts: dict[str, int] = {}
    sample_keys: set[str] = set()
    for member in members[:max_members]:
        name = Path(member.name).name
        parts = name.rsplit(".", 1)
        suffix = parts[1].lower() if len(parts) == 2 else ""
        suffix_counts[suffix] = suffix_counts.get(suffix, 0) + 1
        if parts:
            sample_keys.add(parts[0])
    print("suffix_counts=" + ",".join(f"{k}:{v}" for k, v in sorted(suffix_counts.items())))
    if "jpg" not in suffix_counts and "jpeg" not in suffix_counts and "png" not in suffix_counts:
        warn("no image-like members found in inspected sample")
    examples = sorted(sample_keys)[:5]
    print("sample_keys=" + ",".join(examples))
    for key in examples:
        if len(key) < index_width or not key[-index_width:].isdigit():
            warn(f"sample key {key!r} does not end with {index_width} index digits")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate DALLE2-pytorch WebDataset shard and sidecar embedding layout.")
    parser.add_argument("--tar-pattern", required=True, help="Pattern with one {} slot, e.g. DATA/shards/{}.tar")
    parser.add_argument("--start-shard", type=int, required=True)
    parser.add_argument("--end-shard", type=int, required=True)
    parser.add_argument("--shard-width", type=int, default=6)
    parser.add_argument("--index-width", type=int, required=True)
    parser.add_argument("--image-embeddings", type=Path, default=None, help="Optional sidecar image embedding folder.")
    parser.add_argument("--text-embeddings", type=Path, default=None, help="Optional sidecar text embedding folder.")
    parser.add_argument("--inspect-tar", action="store_true", help="Inspect one tar's member names; use only on small/safe shards.")
    parser.add_argument("--inspect-shard", type=int, default=None, help="Shard number to inspect when --inspect-tar is set. Defaults to start shard.")
    parser.add_argument("--max-members", type=int, default=50, help="Maximum tar members to summarize.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.start_shard > args.end_shard:
        fail("start-shard must be <= end-shard")
    if "{}" not in args.tar_pattern:
        fail("tar-pattern must contain one {} placeholder")
    expected_shards = list(range(args.start_shard, args.end_shard + 1))
    missing_tars: list[Path] = []
    existing_tars: list[Path] = []
    for shard in expected_shards:
        path = format_shard(args.tar_pattern, shard, args.shard_width)
        if path.exists():
            existing_tars.append(path)
        else:
            missing_tars.append(path)

    print(f"expected_shards={len(expected_shards)}")
    print(f"existing_tars={len(existing_tars)}")
    if missing_tars:
        for path in missing_tars[:10]:
            warn(f"missing tar: {path}")
        if len(missing_tars) > 10:
            warn(f"... and {len(missing_tars) - 10} more missing tar files")

    for label, folder in (("image", args.image_embeddings), ("text", args.text_embeddings)):
        if folder is None:
            continue
        files = sidecar_files(folder)
        missing = [shard for shard in expected_shards if shard not in files]
        print(f"{label}_sidecar_files={len(files)}")
        if missing:
            warn(f"{label} sidecar missing shards: {missing[:20]}{'...' if len(missing) > 20 else ''}")

    if args.inspect_tar:
        shard = args.inspect_shard if args.inspect_shard is not None else args.start_shard
        inspect_tar(format_shard(args.tar_pattern, shard, args.shard_width), args.index_width, args.max_members)

    if missing_tars:
        fail("layout check found missing tar files")
    print("OK webdataset-layout")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
