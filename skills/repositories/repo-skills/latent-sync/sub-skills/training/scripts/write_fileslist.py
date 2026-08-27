#!/usr/bin/env python3
"""Write a safe LatentSync training fileslist.

Adapted from the repo's tools/write_fileslist.py, but parameterized and safe:
- no hard-coded private paths;
- recursive .mp4 discovery;
- deterministic sorting and de-duplication;
- explicit --overwrite for existing outputs;
- fail-fast on missing or empty dataset directories.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


VIDEO_SUFFIX = ".mp4"


class FileslistError(RuntimeError):
    """Raised for user-facing fileslist errors."""


def resolve_path(raw: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(raw))).resolve()


def gather_video_paths(dataset_dir: Path) -> list[Path]:
    if not dataset_dir.exists():
        raise FileslistError(f"Dataset directory does not exist: {dataset_dir}")
    if not dataset_dir.is_dir():
        raise FileslistError(f"Dataset path is not a directory: {dataset_dir}")

    paths = [path.resolve() for path in dataset_dir.rglob("*") if path.is_file() and path.suffix.lower() == VIDEO_SUFFIX]
    paths.sort(key=lambda item: str(item))
    if not paths:
        raise FileslistError(f"No .mp4 files found recursively under: {dataset_dir}")
    return paths


def make_output_lines(paths: list[Path], relative_to: Path | None) -> list[str]:
    lines: list[str] = []
    for path in paths:
        if relative_to is None:
            lines.append(str(path))
        else:
            try:
                lines.append(str(path.relative_to(relative_to)))
            except ValueError as exc:
                raise FileslistError(f"Cannot write {path} relative to {relative_to}; choose a broader --relative-to base.") from exc
    return lines


def write_fileslist(output_path: Path, lines: list[str], overwrite: bool) -> None:
    if output_path.exists() and not overwrite:
        raise FileslistError(f"Output already exists: {output_path}. Pass --overwrite to replace it.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a LatentSync .mp4 fileslist from one or more processed dataset directories.")
    parser.add_argument(
        "--dataset-dir",
        action="append",
        required=True,
        help="Processed video directory to scan recursively. Repeat for multiple datasets.",
    )
    parser.add_argument("--output", required=True, help="Fileslist path to write.")
    parser.add_argument(
        "--relative-to",
        default=None,
        help="Optional base directory for relative paths. By default absolute paths are written.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing output fileslist.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    all_paths: list[Path] = []
    seen: set[Path] = set()
    for raw_dir in args.dataset_dir:
        dataset_dir = resolve_path(raw_dir)
        paths = gather_video_paths(dataset_dir)
        print(f"found {len(paths)} .mp4 files under {dataset_dir}", file=sys.stderr)
        for path in paths:
            if path in seen:
                continue
            seen.add(path)
            all_paths.append(path)

    if not all_paths:
        raise SystemExit("No unique .mp4 files found; refusing to write an empty LatentSync fileslist.")

    relative_to = resolve_path(args.relative_to) if args.relative_to else None
    if relative_to is not None and not relative_to.is_dir():
        raise SystemExit(f"--relative-to must be an existing directory: {relative_to}")

    output_path = resolve_path(args.output)
    lines = make_output_lines(all_paths, relative_to)
    write_fileslist(output_path, lines, overwrite=args.overwrite)
    print(f"wrote {len(lines)} unique .mp4 paths to {output_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover
    try:
        raise SystemExit(main())
    except FileslistError as exc:
        raise SystemExit(f"fileslist error: {exc}") from exc
