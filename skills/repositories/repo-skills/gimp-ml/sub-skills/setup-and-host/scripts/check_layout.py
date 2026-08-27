#!/usr/bin/env python3
"""Inspect a generic GIMP-ML-style plug-in and weights layout.

This is a read-only diagnostic. It never imports plug-ins, contacts a network,
creates directories, downloads assets, changes permissions, or starts GIMP.
"""

from __future__ import annotations

import argparse
import os
import stat
from pathlib import Path
from typing import Iterable

EXPECTED_FILES = {
    "deepmatting/stage1_sad_57.1.pth",
    "MiDaS/model.pt",
    "colorize/caffemodel.pth",
    "super_resolution/model_srresnet.pth",
    "faceparse/79999_iter.pth",
    "deblur/mymodel.pth",
    "deblur/best_fpn.h5",
    "deeplabv3/deeplabv3+model.pt",
    "facegen/label2face_512p/latest_net_G.pth",
    "deepdehaze/dehazer.pth",
    "deepdenoise/est_net.pth",
    "deepdenoise/net.pth",
    "enlightening/200_net_G_A.pth",
    "interpolateframes/contextnet.pkl",
    "interpolateframes/flownet.pkl",
    "interpolateframes/unet.pkl",
    "inpainting/model_places2.pth",
    "inpainting/refinement.pth",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only inspection of a supplied plug-in root, its weights "
            "directory, and an optional legacy environment."
        )
    )
    parser.add_argument(
        "plugin_root",
        metavar="PATH",
        help="explicit plug-in root to inspect",
    )
    parser.add_argument(
        "--weights-root",
        metavar="PATH",
        help="weights directory; default is PLUGIN_ROOT/weights",
    )
    parser.add_argument(
        "--env-root",
        metavar="PATH",
        help="legacy environment directory; default is PLUGIN_ROOT/gimpenv",
    )
    parser.add_argument(
        "--expected-file",
        action="append",
        metavar="RELATIVE_PATH",
        help=(
            "additional relative file below WEIGHTS_ROOT to check; may be "
            "repeated"
        ),
    )
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return str(path.resolve())
    except OSError:
        return str(path)


def readable(path: Path) -> str:
    if not path.exists():
        return "missing"
    if not os.access(path, os.R_OK):
        return "not-readable"
    return "readable"


def mode(path: Path) -> str:
    try:
        return stat.filemode(path.stat().st_mode)
    except OSError:
        return "?---------"


def iter_children(path: Path) -> Iterable[Path]:
    try:
        return sorted(path.iterdir(), key=lambda item: item.name.lower())
    except OSError:
        return ()


def inspect(args: argparse.Namespace) -> int:
    plugin_root = Path(args.plugin_root).expanduser()
    weights_root = (
        Path(args.weights_root).expanduser()
        if args.weights_root
        else plugin_root / "weights"
    )
    env_root = (
        Path(args.env_root).expanduser()
        if args.env_root
        else plugin_root / "gimpenv"
    )

    print("READ_ONLY layout check")
    print(f"plugin_root: {display_path(plugin_root)}")
    if not plugin_root.exists():
        print("plugin_root_status: missing (no changes made)")
        return 0
    if not plugin_root.is_dir():
        print("plugin_root_status: not-a-directory (no changes made)")
        return 0
    print(f"plugin_root_status: present mode={mode(plugin_root)}")

    py_files = [
        child
        for child in iter_children(plugin_root)
        if child.is_file() and child.suffix.lower() == ".py"
    ]
    executable = sum(os.access(path, os.X_OK) for path in py_files)
    print(f"top_level_python_files: {len(py_files)}")
    print(f"top_level_python_executable: {executable}/{len(py_files)}")
    for path in py_files:
        print(f"  python: {path.name} mode={mode(path)} {readable(path)}")

    print(f"weights_root: {display_path(weights_root)}")
    if not weights_root.exists():
        print("weights_status: missing (assets not downloaded)")
    elif not weights_root.is_dir():
        print("weights_status: not-a-directory")
    else:
        print(f"weights_status: present mode={mode(weights_root)} {readable(weights_root)}")
        model_dirs = [child for child in iter_children(weights_root) if child.is_dir()]
        print(f"weight_model_directories: {len(model_dirs)}")
        for path in model_dirs:
            print(f"  model_dir: {path.name} mode={mode(path)} {readable(path)}")

        expected = set(EXPECTED_FILES)
        expected.update(args.expected_file or [])
        for relative in sorted(expected):
            # Deliberately keep this a lexical relative check; no write follows
            # even if a caller supplies ".." in an additional expectation.
            candidate = weights_root / relative
            if candidate.is_file():
                print(f"  expected_file: present {relative} {mode(candidate)} {readable(candidate)}")
            else:
                print(f"  expected_file: missing {relative}")

    print(f"legacy_env_root: {display_path(env_root)}")
    if not env_root.exists():
        print("legacy_env_status: missing")
    elif not env_root.is_dir():
        print("legacy_env_status: not-a-directory")
    else:
        print(f"legacy_env_status: present mode={mode(env_root)} {readable(env_root)}")
        python2_markers = [
            env_root / "bin" / "python",
            env_root / "Scripts" / "python.exe",
            env_root / "lib" / "python2.7",
        ]
        for marker in python2_markers:
            print(f"  env_marker: {marker} {'present' if marker.exists() else 'missing'}")

    print("result: inspection complete; presence is not proof of compatibility or model integrity")
    return 0


def main() -> int:
    try:
        return inspect(parse_args())
    except (OSError, ValueError) as exc:
        # A supplied unreadable path is a diagnostic result, not a reason to
        # perform a recovery action.
        print(f"diagnostic_error: {exc}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
