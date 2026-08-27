#!/usr/bin/env python3
"""Safe skill-layer sidecar writer for selected DeepDanbooru tags.

The native 1.0.0 ``evaluate --save-txt`` path can fail when no tags pass the
threshold and opens existing sidecars in ``w`` mode. This helper makes both
choices explicit without modifying the installed package: empty selections
are rejected before touching a sidecar, and replacement requires an explicit
flag.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable


def sidecar_path(image_path: Path) -> Path:
    """Return the sibling text sidecar used by DeepDanbooru."""
    return image_path.with_suffix(".txt")


def write_sidecar(
    image_path: Path,
    tags: Iterable[str],
    *,
    allow_overwrite: bool = False,
) -> Path:
    """Write selected tags, refusing empty output and unsafe replacement.

    The file is not created or changed when ``tags`` is empty. Existing regular
    files are preserved unless ``allow_overwrite=True`` is supplied explicitly;
    a directory at the sidecar path is always rejected.
    """
    selected = list(tags)
    if not selected:
        raise ValueError("refusing to write an empty tag sidecar")

    output = sidecar_path(image_path)
    if output.exists() and output.is_dir():
        raise IsADirectoryError(f"sidecar path is a directory: {output}")
    if output.exists() and not allow_overwrite:
        raise FileExistsError(
            f"sidecar already exists; pass allow_overwrite=True to replace: {output}"
        )
    output.write_text(", ".join(selected), encoding="utf-8")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="Image whose sibling .txt is written.")
    parser.add_argument("tags", nargs="*", help="Selected tags, in model/tag-file order.")
    parser.add_argument(
        "--allow-overwrite",
        action="store_true",
        help="Replace an existing sidecar; default is to refuse.",
    )
    args = parser.parse_args(argv)
    try:
        output = write_sidecar(
            args.image, args.tags, allow_overwrite=args.allow_overwrite
        )
    except (FileExistsError, IsADirectoryError, ValueError) as exc:
        parser.error(str(exc))
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
