#!/usr/bin/env python3
"""Create a tiny X-AnyLabeling conversion fixture.

The fixture is intentionally self-contained and does not depend on repository
assets. It creates:
  - images/tiny.png: a 10x10 RGB image
  - labels/tiny.txt: one YOLO detection label
  - classes.txt: one class named "box"
  - xlabel/: empty directory for conversion output
"""

from __future__ import annotations

import argparse
import base64
from pathlib import Path

# 10x10 white PNG generated once and embedded to avoid any third-party image
# dependency. The exact pixels are irrelevant for YOLO-to-XLABEL conversion;
# only readable dimensions matter.
_TINY_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAAFElEQVR4nGP8//8/A27AhEduBEsDABbHC"
    "T1NnJ9WAAAAAElFTkSuQmCC"
)


def create_fixture(output_dir: Path, overwrite: bool = False) -> dict[str, Path]:
    output_dir = output_dir.expanduser().resolve()
    images_dir = output_dir / "images"
    labels_dir = output_dir / "labels"
    xlabel_dir = output_dir / "xlabel"

    for directory in (images_dir, labels_dir, xlabel_dir):
        directory.mkdir(parents=True, exist_ok=True)

    image_file = images_dir / "tiny.png"
    label_file = labels_dir / "tiny.txt"
    classes_file = output_dir / "classes.txt"

    if overwrite or not image_file.exists():
        image_file.write_bytes(base64.b64decode(_TINY_PNG_BASE64))

    if overwrite or not label_file.exists():
        # class=0, centered box at (5,5), width=4, height=4 in a 10x10 image.
        label_file.write_text("0 0.5 0.5 0.4 0.4\n", encoding="utf-8")

    if overwrite or not classes_file.exists():
        classes_file.write_text("box\n", encoding="utf-8")

    return {
        "work_dir": output_dir,
        "images": images_dir,
        "labels": labels_dir,
        "output": xlabel_dir,
        "classes": classes_file,
        "image_file": image_file,
        "label_file": label_file,
        "expected_json": xlabel_dir / "tiny.json",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory where the tiny conversion fixture should be created.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Rewrite fixture files if they already exist.",
    )
    args = parser.parse_args()

    paths = create_fixture(args.output_dir, overwrite=args.overwrite)
    for name, path in paths.items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
