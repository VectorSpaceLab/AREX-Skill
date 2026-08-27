#!/usr/bin/env python3
"""Safe PySOT tracking input validator.

This helper validates config/snapshot/media/dataset inputs and prints a command
skeleton for PySOT demo/test workflows. It intentionally does not import PySOT,
OpenCV, PyTorch, load model weights, open GUI windows, download datasets, or run
tracking.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shlex
import sys
from typing import Any, Dict, Iterable, List, Optional, Tuple

SUPPORTED_TRACK_TYPES = {"SiamRPNTracker", "SiamMaskTracker", "SiamRPNLTTracker"}
COMMON_TOP_LEVEL_SECTIONS = ("META_ARC", "BACKBONE", "RPN", "ANCHOR", "TRACK")
IMAGE_SUFFIXES = {".jpg", ".jpeg"}
VIDEO_SUFFIXES = {".avi", ".mp4"}


def q(value: object) -> str:
    return shlex.quote(str(value))


def add_error(errors: List[str], message: str) -> None:
    errors.append(f"ERROR: {message}")


def add_warning(warnings: List[str], message: str) -> None:
    warnings.append(f"WARNING: {message}")


def load_yaml_mapping(path: Path, errors: List[str], warnings: List[str]) -> Tuple[Dict[str, Any], Optional[str]]:
    """Load YAML when PyYAML is present; otherwise return a minimal scan.

    The fallback is deliberately small but enough to detect top-level sections and
    TRACK.TYPE in normal PySOT config files.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            text = path.read_text()
        except Exception as exc:  # pragma: no cover - defensive
            add_error(errors, f"cannot read config {path}: {exc}")
            return {}, None
    except OSError as exc:
        add_error(errors, f"cannot read config {path}: {exc}")
        return {}, None

    try:
        import yaml  # type: ignore
    except Exception:
        add_warning(warnings, "PyYAML is not importable; using a conservative text scan for TRACK.TYPE")
        return minimal_yaml_scan(text), None

    try:
        data = yaml.safe_load(text)
    except Exception as exc:
        add_error(errors, f"config is not valid YAML: {exc}")
        return {}, None

    if data is None:
        add_error(errors, "config YAML is empty")
        return {}, None
    if not isinstance(data, dict):
        add_error(errors, "config YAML top level must be a mapping")
        return {}, None
    return data, text


def minimal_yaml_scan(text: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    current_top: Optional[str] = None
    current_indent = 0
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"\'')
        if indent == 0:
            if value == "":
                data.setdefault(key, {})
                current_top = key
                current_indent = indent
            else:
                data[key] = value
                current_top = None
        elif current_top and indent > current_indent:
            section = data.setdefault(current_top, {})
            if isinstance(section, dict):
                section[key] = value
    return data


def nested_get(mapping: Dict[str, Any], keys: Iterable[str]) -> Optional[Any]:
    cur: Any = mapping
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def validate_config(path: Path, errors: List[str], warnings: List[str]) -> Optional[str]:
    if not path.exists():
        add_error(errors, f"config file does not exist: {path}")
        return None
    if not path.is_file():
        add_error(errors, f"config path is not a file: {path}")
        return None

    data, _ = load_yaml_mapping(path, errors, warnings)
    if errors:
        return None

    missing_sections = [section for section in COMMON_TOP_LEVEL_SECTIONS if section not in data]
    if missing_sections:
        add_warning(
            warnings,
            "config omits common PySOT sections "
            + ", ".join(missing_sections)
            + "; PySOT defaults may fill them, but verify this is intentional",
        )

    track_type = nested_get(data, ("TRACK", "TYPE"))
    if track_type is None or str(track_type).strip() == "":
        add_warning(warnings, "TRACK.TYPE is not set; PySOT default is SiamRPNTracker")
        return "SiamRPNTracker"

    track_type_str = str(track_type).strip().strip('"\'')
    if track_type_str not in SUPPORTED_TRACK_TYPES:
        add_error(
            errors,
            "unsupported TRACK.TYPE "
            f"{track_type_str!r}; supported values are {', '.join(sorted(SUPPORTED_TRACK_TYPES))}",
        )
    return track_type_str


def validate_snapshot(path: Path, errors: List[str], warnings: List[str]) -> None:
    if not path.exists():
        add_error(
            errors,
            f"snapshot file does not exist: {path}. Provide a downloaded/trained .pth file matching the config.",
        )
        return
    if not path.is_file():
        add_error(errors, f"snapshot path is not a file: {path}")
        return
    if path.suffix.lower() not in {".pth", ".pt", ".ckpt"}:
        add_warning(warnings, f"snapshot extension {path.suffix!r} is unusual for PySOT; expected a .pth-style checkpoint")


def validate_demo_media(video_name: Optional[str], image_dir: Optional[str], errors: List[str], warnings: List[str]) -> Optional[Path]:
    if video_name and image_dir:
        add_error(errors, "use only one of --video-name or --image-dir; both map to demo.py --video_name")
        return None
    if image_dir:
        path = Path(image_dir).expanduser()
        if not path.exists():
            add_error(errors, f"image directory does not exist: {path}")
            return path
        if not path.is_dir():
            add_error(errors, f"--image-dir is not a directory: {path}")
            return path
        images = sorted(p for p in path.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
        if not images:
            add_error(errors, f"image directory contains no .jpg/.jpeg frames: {path}")
        non_numeric = [p.name for p in images if not p.stem.isdigit()]
        if non_numeric:
            add_warning(
                warnings,
                "demo.py sorts image frames by int(filename stem); non-numeric stems may fail: "
                + ", ".join(non_numeric[:5]),
            )
        return path
    if video_name:
        path = Path(video_name).expanduser()
        if not path.exists():
            add_error(errors, f"video/input path does not exist: {path}")
            return path
        if path.is_dir():
            add_warning(warnings, "--video-name points to a directory; treating it as an image sequence input")
            images = sorted(p for p in path.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
            if not images:
                add_error(errors, f"input directory contains no .jpg/.jpeg frames: {path}")
            return path
        if not path.is_file():
            add_error(errors, f"--video-name is neither a file nor a directory: {path}")
            return path
        if path.suffix.lower() not in VIDEO_SUFFIXES:
            add_warning(warnings, f"native demo.py recognizes .avi/.mp4 by suffix; {path.name!r} may be treated as an image directory")
        return path
    add_warning(warnings, "no demo media supplied; native demo will try webcam 0 and open an OpenCV ROI window")
    return None


def resolve_dataset_dir(dataset: Optional[str], repo_root: Path) -> Optional[Path]:
    if not dataset:
        return None
    raw = Path(dataset).expanduser()
    if raw.exists() or os.sep in dataset or (os.altsep and os.altsep in dataset):
        return raw
    return repo_root / "testing_dataset" / dataset


def validate_dataset(dataset: Optional[str], repo_root: Path, mode: str, errors: List[str], warnings: List[str]) -> Optional[Path]:
    if not dataset:
        if mode == "test":
            add_warning(warnings, "--dataset is required before running native test.py; skeleton will use <DATASET>")
        return None
    dataset_dir = resolve_dataset_dir(dataset, repo_root)
    if dataset_dir is None:
        return None
    if not dataset_dir.exists():
        add_error(errors, f"dataset directory does not exist: {dataset_dir}")
    elif not dataset_dir.is_dir():
        add_error(errors, f"dataset path is not a directory: {dataset_dir}")
    return dataset_dir


def command_skeleton(args: argparse.Namespace, media_arg: Optional[Path]) -> str:
    config = q(args.config)
    snapshot = q(args.snapshot)
    repo_root_path = Path(args.repo_root)
    repo_root = q(repo_root_path)
    demo_script = q(repo_root_path / "tools" / "demo.py")
    test_script = q(repo_root_path / "tools" / "test.py")
    dataset = q(args.dataset) if args.dataset else "<DATASET>"

    if args.mode == "demo":
        pieces = [
            f"PYTHONPATH={repo_root}:$PYTHONPATH",
            f"python {demo_script}",
            f"--config {config}",
            f"--snapshot {snapshot}",
        ]
        if media_arg is not None:
            pieces.append(f"--video_name {q(media_arg)}")
        return " \\\n  ".join(pieces)

    pieces = [
        f"PYTHONPATH={repo_root}:$PYTHONPATH",
        f"python -u {test_script}",
        f"--dataset {dataset}",
        f"--config {config}",
        f"--snapshot {snapshot}",
    ]
    if args.video_name:
        pieces.append(f"--video {q(args.video_name)}")
    return " \\\n  ".join(pieces)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate PySOT tracking inputs and print a safe demo/test command skeleton without running tracking.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--config", required=True, help="Path to a PySOT config YAML")
    parser.add_argument("--snapshot", required=True, help="Path to a PySOT model snapshot/checkpoint")
    parser.add_argument("--video-name", help="Optional demo video path, image-sequence directory, or test video name")
    parser.add_argument("--image-dir", help="Optional demo image-sequence directory; mutually exclusive with --video-name")
    parser.add_argument("--dataset", help="Optional benchmark dataset name or dataset directory")
    parser.add_argument("--mode", choices=("demo", "test"), default="demo", help="Workflow to validate/construct")
    parser.add_argument(
        "--repo-root",
        default=".",
        help="PySOT checkout root used for PYTHONPATH, tools path, and testing_dataset/<DATASET> lookup",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    errors: List[str] = []
    warnings: List[str] = []

    config_path = Path(args.config).expanduser()
    snapshot_path = Path(args.snapshot).expanduser()
    repo_root = Path(args.repo_root).expanduser()
    args.repo_root = str(repo_root)

    track_type = validate_config(config_path, errors, warnings)
    validate_snapshot(snapshot_path, errors, warnings)

    media_arg: Optional[Path] = None
    if args.mode == "demo":
        media_arg = validate_demo_media(args.video_name, args.image_dir, errors, warnings)
        if args.dataset:
            add_warning(warnings, "--dataset is ignored for demo mode")
    else:
        if args.image_dir:
            add_warning(warnings, "--image-dir is ignored for test mode; use --video-name for a dataset video name filter")
        validate_dataset(args.dataset, repo_root, args.mode, errors, warnings)

    print("PySOT tracking input validation")
    print(f"mode: {args.mode}")
    print(f"config: {config_path}")
    print(f"snapshot: {snapshot_path}")
    if track_type:
        print(f"TRACK.TYPE: {track_type}")
    if args.dataset:
        print(f"dataset: {args.dataset}")
    if media_arg is not None:
        print(f"demo input: {media_arg}")

    for warning in warnings:
        print(warning, file=sys.stderr)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("validation: failed")
        return 2

    print("validation: ok")
    print("\nSafe command skeleton (review before running):")
    print(command_skeleton(args, media_arg))
    if args.mode == "test":
        print("\nNOTE: Native tools/test.py calls .cuda(); full benchmark runs require CUDA plus user-supplied dataset/snapshot artifacts.")
    elif media_arg is None:
        print("\nNOTE: Native demo without --video_name opens webcam 0 and an OpenCV ROI-selection window.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
