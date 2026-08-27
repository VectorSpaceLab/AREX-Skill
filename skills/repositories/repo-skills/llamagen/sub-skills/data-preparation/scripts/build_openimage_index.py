#!/usr/bin/env python3
"""Build a safe OpenImages-style image_paths.json manifest."""

from __future__ import annotations

import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable

from PIL import Image

DEFAULT_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]


def normalize_extensions(raw_extensions: Iterable[str]) -> set[str]:
    normalized: set[str] = set()
    for extension in raw_extensions:
        ext = extension.strip().lower()
        if not ext:
            continue
        if not ext.startswith("."):
            ext = f".{ext}"
        normalized.add(ext)
    return normalized


def build_folder_names(prefix: str, start: int, end: int, width: int) -> list[str]:
    if end < start:
        raise ValueError(f"folder-end ({end}) must be >= folder-start ({start})")
    return [f"{prefix}{index:0{width}d}" for index in range(start, end + 1)]


def verify_image(image_path: Path) -> tuple[bool, str | None]:
    try:
        with Image.open(image_path) as image:
            image.verify()
        return True, None
    except Exception as exc:  # noqa: BLE001 - report the underlying image error verbatim
        return False, str(exc)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a relative OpenImages image-path manifest with optional strict validation."
    )
    parser.add_argument("--data-path", type=str, required=True)
    parser.add_argument("--output-path", type=str, default="image_paths.json")
    parser.add_argument("--folder-prefix", type=str, default="openimages_")
    parser.add_argument("--folder-start", type=int, default=1)
    parser.add_argument("--folder-end", type=int, default=47)
    parser.add_argument("--folder-width", type=int, default=4)
    parser.add_argument("--extensions", nargs="+", default=DEFAULT_EXTENSIONS)
    parser.add_argument("--workers", type=int, default=max((os.cpu_count() or 1) // 2, 4))
    parser.add_argument("--strict", action="store_true", help="fail on missing folders or unreadable images")
    args = parser.parse_args()

    data_path = Path(args.data_path).expanduser().resolve()
    if not data_path.is_dir():
        raise NotADirectoryError(f"data path does not exist or is not a directory: {data_path}")

    output_path = Path(args.output_path).expanduser()
    if not output_path.is_absolute():
        output_path = data_path / output_path

    extensions = normalize_extensions(args.extensions)
    folder_names = build_folder_names(args.folder_prefix, args.folder_start, args.folder_end, args.folder_width)

    candidate_paths: list[str] = []
    missing_folders: list[str] = []
    for folder_name in folder_names:
        folder_path = data_path / folder_name
        if not folder_path.is_dir():
            missing_folders.append(folder_name)
            continue
        for entry in sorted(folder_path.iterdir()):
            if entry.is_file() and entry.suffix.lower() in extensions:
                candidate_paths.append(f"{folder_name}/{entry.name}")

    if not candidate_paths:
        raise RuntimeError(
            "no candidate images were found; check the folder prefix, folder range, and file extensions"
        )

    print(f"[info] collected {len(candidate_paths)} candidate image paths from {len(folder_names)} folders")
    if missing_folders:
        print(f"[warn] missing folders: {', '.join(missing_folders)}")

    valid_paths: list[str] = []
    bad_entries: list[tuple[str, str]] = []
    max_workers = max(1, args.workers)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(verify_image, data_path / rel_path): rel_path for rel_path in candidate_paths
        }
        for future in as_completed(futures):
            rel_path = futures[future]
            ok, error = future.result()
            if ok:
                valid_paths.append(rel_path)
            else:
                bad_entries.append((rel_path, error or "unknown image error"))
                print(f"[warn] skipping unreadable image: {rel_path} ({error})")

    valid_paths.sort()

    if args.strict and (missing_folders or bad_entries):
        message_lines = ["OpenImages manifest validation failed:"]
        if missing_folders:
            message_lines.append(f"- missing folders: {', '.join(missing_folders)}")
        if bad_entries:
            bad_preview = ", ".join(rel_path for rel_path, _ in bad_entries[:10])
            extra = "" if len(bad_entries) <= 10 else f" ... (+{len(bad_entries) - 10} more)"
            message_lines.append(f"- unreadable images: {bad_preview}{extra}")
        raise RuntimeError("\n".join(message_lines))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(valid_paths, handle, indent=4)

    print(f"[info] wrote {len(valid_paths)} image paths to {output_path}")
    if bad_entries:
        print(f"[info] skipped {len(bad_entries)} unreadable image(s)")


if __name__ == "__main__":
    main()
