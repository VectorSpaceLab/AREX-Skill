#!/usr/bin/env python3
"""Probe the create-project contract in a safe temporary directory.

This deliberately does not import DeepDanbooru or invoke a checkout. It writes
exactly the default project.json contract, reads it back, and verifies that the
project starts without tags, images, or a database. Use an explicit empty
--output-dir to retain the probe; the default is cleaned up on success.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path


DEFAULT_PROJECT_CONTEXT = {
    "image_width": 299,
    "image_height": 299,
    "database_path": None,
    "minimum_tag_count": 20,
    "model": "resnet_custom_v2",
    "minibatch_size": 32,
    "epoch_count": 10,
    "export_model_per_epoch": 10,
    "checkpoint_frequency_mb": 200,
    "console_logging_frequency_mb": 10,
    "loss": "binary_crossentropy",
    "optimizer": "adam",
    "learning_rate": 0.001,
    "rotation_range": [0.0, 360.0],
    "scale_range": [0.9, 1.1],
    "shift_range": [-0.1, 0.1],
    "mixed_precision": False,
}


def _destination(args: argparse.Namespace) -> tuple[Path, bool]:
    if args.output_dir is not None:
        destination = args.output_dir.expanduser().resolve()
        if destination.exists() and not destination.is_dir():
            raise ValueError(f"output path is not a directory: {destination}")
        if destination.exists() and any(destination.iterdir()):
            raise ValueError(
                f"refusing to use non-empty output directory: {destination}"
            )
        destination.mkdir(parents=True, exist_ok=True)
        return destination, False

    destination = Path(tempfile.mkdtemp(prefix="deepdanbooru-project-probe-"))
    return destination, not args.keep


def run_probe(destination: Path) -> None:
    project_file = destination / "project.json"
    project_file.write_text(
        json.dumps(DEFAULT_PROJECT_CONTEXT, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )
    loaded = json.loads(project_file.read_text(encoding="utf-8"))
    if loaded != DEFAULT_PROJECT_CONTEXT:
        raise AssertionError("project.json did not round-trip the default context")
    if loaded["database_path"] is not None:
        raise AssertionError("new projects must leave database_path as null")
    unexpected = [name for name in ("tags.txt", "images") if (destination / name).exists()]
    if unexpected:
        raise AssertionError(f"probe unexpectedly created: {', '.join(unexpected)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Safely probe the DeepDanbooru create-project file contract."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Use an empty directory instead of a temporary directory; never overwritten.",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the default temporary directory after a successful probe.",
    )
    args = parser.parse_args(argv)

    destination: Path | None = None
    remove_after = False
    try:
        destination, remove_after = _destination(args)
        run_probe(destination)
        print(f"PASS: project contract probe ({destination})")
        return 0
    except (OSError, ValueError, AssertionError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    finally:
        if remove_after and destination is not None:
            shutil.rmtree(destination, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
