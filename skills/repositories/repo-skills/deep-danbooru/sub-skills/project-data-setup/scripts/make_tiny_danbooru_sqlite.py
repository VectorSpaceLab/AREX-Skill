#!/usr/bin/env python3
"""Create a deterministic, tiny Danbooru-like SQLite fixture and image tree."""

from __future__ import annotations

import argparse
import base64
import shutil
import sqlite3
import sys
from pathlib import Path

# Valid 1x1 payloads make the accepted image paths useful for layout probes.
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)
JPEG_1X1 = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAX/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAH/AP/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAQUCf//EABQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQMBAT8Bf//EABQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQEBBj8Cf//Z"
)

ROWS = [
    (1, "0123456789abcdef0123456789abcdef", "jpg", "1girl long_hair", 2, "g", 5, 0),
    (2, "ab0123456789abcdef0123456789abcdef", "png", "1girl blue_hair", 2, "s", -1, 0),
    (3, "cd0123456789abcdef0123456789abcdef", "jpeg", "short_hair", 1, "q", 0, 0),
    (4, "ef0123456789abcdef0123456789abcdef", "jpg", "deleted_tag", 3, "e", 9, 1),
    (5, "ff0123456789abcdef0123456789abcdef", "gif", "ignored_extension", 99, "g", 1, 0),
]

SCHEMA = """
CREATE TABLE posts (
    id INTEGER NOT NULL PRIMARY KEY,
    md5 TEXT,
    file_ext TEXT,
    tag_string TEXT,
    tag_count_general INTEGER,
    rating TEXT,
    score INTEGER,
    is_deleted INTEGER
)
"""


def prepare_directory(path: Path, overwrite: bool) -> None:
    if path.exists():
        if not path.is_dir():
            raise ValueError(f"output path is not a directory: {path}")
        if overwrite:
            shutil.rmtree(path)
        elif any(path.iterdir()):
            raise ValueError(
                f"refusing to overwrite non-empty directory: {path}; use --overwrite explicitly"
            )
    path.mkdir(parents=True, exist_ok=True)


def make_fixture(root: Path) -> None:
    images = root / "images"
    images.mkdir()
    database = root / "source.sqlite"
    connection = sqlite3.connect(database)
    try:
        connection.executescript(SCHEMA)
        connection.executemany(
            """INSERT INTO posts
               (id, md5, file_ext, tag_string, tag_count_general, rating, score, is_deleted)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ROWS,
        )
        connection.commit()
    finally:
        connection.close()

    for _post_id, md5, extension, _tags, _count, _rating, _score, deleted in ROWS:
        # Keep a file for all supported rows, including the deleted one. The
        # gif row intentionally has no file because the loader ignores it.
        if extension not in {"png", "jpg", "jpeg"}:
            continue
        image_path = images / md5[:2] / f"{md5}.{extension}"
        image_path.parent.mkdir(parents=True, exist_ok=True)
        image_path.write_bytes(PNG_1X1 if extension == "png" else JPEG_1X1)

    (root / "fixture-info.txt").write_text(
        "Deterministic DeepDanbooru fixture.\n"
        "source.sqlite contains five source rows: one deleted and one unsupported GIF.\n"
        "Image payloads are valid 1x1 PNG/JPEG files.\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a tiny offline Danbooru-like SQLite fixture and images/ tree."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("deepdanbooru-tiny-fixture"),
        help="New fixture directory (default: ./deepdanbooru-tiny-fixture).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Explicitly remove an existing non-empty output directory first.",
    )
    args = parser.parse_args(argv)
    root = args.output_dir.expanduser().resolve()
    try:
        prepare_directory(root, args.overwrite)
        make_fixture(root)
    except (OSError, ValueError, sqlite3.Error) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: fixture created at {root}")
    print(f"  source: {root / 'source.sqlite'}")
    print(f"  images: {root / 'images'}")
    print("  rows: 5 (4 supported image extensions, 1 ignored GIF; 1 deleted)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
