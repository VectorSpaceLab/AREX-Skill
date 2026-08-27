#!/usr/bin/env python3
"""Render UniAD nuScenes data-info conversion commands without executing them.

This helper is self-contained and does not import UniAD. It mirrors the public
UniAD data wrapper semantics: create temporal nuScenes info PKLs by invoking
`tools/create_data.py nuscenes` with the appropriate root, CAN bus, output,
prefix, and version arguments.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def q(value: object) -> str:
    """Shell-quote a value."""
    return shlex.quote(str(value))


def default_paths(args: argparse.Namespace) -> Dict[str, str]:
    root = Path(args.uniad_root)
    if args.style == "absolute":
        repo = root.expanduser().resolve()
        return {
            "uniad_root": str(repo),
            "converter": str(Path(args.converter).expanduser().resolve())
            if args.converter
            else str(repo / "tools" / "create_data.py"),
            "root_path": str(Path(args.root_path).expanduser().resolve())
            if args.root_path
            else str(repo / "data" / "nuscenes"),
            "canbus": str(Path(args.canbus).expanduser().resolve())
            if args.canbus
            else str(repo / "data" / "nuscenes"),
            "out_dir": str(Path(args.out_dir).expanduser().resolve())
            if args.out_dir
            else str(repo / "data" / "infos"),
        }

    return {
        "uniad_root": str(root),
        "converter": args.converter or "tools/create_data.py",
        "root_path": args.root_path or "data/nuscenes",
        "canbus": args.canbus or "data/nuscenes",
        "out_dir": args.out_dir or "data/infos",
    }


def expected_outputs(version: str, out_dir: str, prefix: str) -> List[str]:
    out = Path(out_dir)
    if version == "v1.0-mini":
        return [
            str(out / f"{prefix}_infos_temporal_train.pkl"),
            str(out / f"{prefix}_infos_temporal_val.pkl"),
            str(out / f"{prefix}_infos_temporal_train_mono3d.coco.json"),
            str(out / f"{prefix}_infos_temporal_val_mono3d.coco.json"),
        ]
    return [
        str(out / f"{prefix}_infos_temporal_train.pkl"),
        str(out / f"{prefix}_infos_temporal_val.pkl"),
        str(out / f"{prefix}_infos_temporal_test.pkl"),
        str(out / f"{prefix}_infos_temporal_train_mono3d.coco.json"),
        str(out / f"{prefix}_infos_temporal_val_mono3d.coco.json"),
        str(out / f"{prefix}_infos_temporal_test_mono3d.coco.json"),
    ]


def build_shell(args: argparse.Namespace, paths: Dict[str, str]) -> str:
    py = q(args.python)
    converter = q(paths["converter"])
    root_path = q(paths["root_path"])
    canbus = q(paths["canbus"])
    out_dir = q(paths["out_dir"])
    extra_tag = q(args.extra_tag)
    version = q(args.version)
    max_sweeps = q(args.max_sweeps)

    body = (
        f"{py} {converter} nuscenes "
        f"--root-path {root_path} "
        f"--out-dir {out_dir} "
        f"--extra-tag {extra_tag} "
        f"--version {version} "
        f"--canbus {canbus} "
        f"--max-sweeps {max_sweeps}"
    )

    if args.style == "relative":
        setup = []
        if not args.no_mkdir:
            setup.append(f"mkdir -p {out_dir}")
        setup.append(f"PYTHONPATH=\"$PWD:${{PYTHONPATH:-}}\" {body}")
        return f"cd {q(paths['uniad_root'])} && " + " && ".join(setup)

    setup = []
    if not args.no_mkdir:
        setup.append(f"mkdir -p {out_dir}")
    setup.append(f"PYTHONPATH={q(paths['uniad_root'])}:\"${{PYTHONPATH:-}}\" {body}")
    return " && ".join(setup)


def check_inputs(paths: Dict[str, str]) -> Tuple[List[str], List[str]]:
    warnings: List[str] = []
    notes: List[str] = []
    repo = Path(paths["uniad_root"])
    converter = Path(paths["converter"])
    root_path = Path(paths["root_path"])
    canbus = Path(paths["canbus"])

    if not repo.exists():
        warnings.append(f"UniAD root does not exist: {repo}")
    if not converter.exists():
        warnings.append(f"Converter script is not present at render time: {converter}")
    if not root_path.exists():
        warnings.append(f"nuScenes root is not present at render time: {root_path}")
    if not canbus.exists():
        warnings.append(f"CAN bus root is not present at render time: {canbus}")
    if not warnings:
        notes.append("Input paths exist at render time; this still does not prove conversion dependencies or full data completeness.")
    return warnings, notes


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Dry-run renderer for UniAD nuScenes temporal info-PKL generation. "
            "The rendered command is not executed."
        )
    )
    parser.add_argument("--uniad-root", default=".", help="UniAD repository root used for command rendering; default: current directory.")
    parser.add_argument("--style", choices=["relative", "absolute"], default="relative", help="Render paths relative to --uniad-root or as absolute paths.")
    parser.add_argument("--python", default="python", help="Python executable to place in the rendered command.")
    parser.add_argument("--converter", help="Path to create_data.py. Default: tools/create_data.py under --uniad-root.")
    parser.add_argument("--root-path", help="nuScenes dataroot. Default: data/nuscenes under --uniad-root.")
    parser.add_argument("--canbus", help="Root containing can_bus. Default: same as --root-path.")
    parser.add_argument("--out-dir", help="Directory for generated info PKLs. Default: data/infos under --uniad-root.")
    parser.add_argument("--extra-tag", default="nuscenes", help="Info-file prefix; default creates nuscenes_infos_temporal_*.pkl.")
    parser.add_argument("--version", choices=["v1.0", "v1.0-mini"], default="v1.0", help="Wrapper version argument. v1.0 processes trainval and test; v1.0-mini processes mini only.")
    parser.add_argument("--max-sweeps", type=int, default=10, help="Maximum lidar sweeps per sample; UniAD default is 10.")
    parser.add_argument("--no-mkdir", action="store_true", help="Do not include the mkdir -p out-dir precommand.")
    parser.add_argument("--check-inputs", action="store_true", help="Check whether rendered paths exist, without requiring them to exist by default.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a human-readable dry-run report.")
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    paths = default_paths(args)
    command = build_shell(args, paths)
    outputs = expected_outputs(args.version, paths["out_dir"], args.extra_tag)
    warnings: List[str] = []
    notes: List[str] = [
        "Dry run only: this helper renders a command and never executes UniAD conversion.",
        "Raw nuScenes, CAN bus, map files, and conversion dependencies must already be available before running the rendered command.",
        "If generated PKLs contain root-prefixed paths, the active UniAD config may need data_root = \"\" instead of data_root = \"data/nuscenes/\".",
    ]

    if args.check_inputs:
        path_warnings, path_notes = check_inputs(paths)
        warnings.extend(path_warnings)
        notes.extend(path_notes)

    payload = {
        "status": "warning" if warnings else "ok",
        "command": command,
        "paths": paths,
        "version_semantics": (
            "v1.0-mini only" if args.version == "v1.0-mini" else "v1.0 wrapper processes v1.0-trainval and v1.0-test"
        ),
        "expected_outputs": outputs,
        "warnings": warnings,
        "notes": notes,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("UniAD data conversion command dry run")
        print("====================================")
        print(command)
        print("\nExpected outputs:")
        for item in outputs:
            print(f"  - {item}")
        if warnings:
            print("\nWarnings:")
            for item in warnings:
                print(f"  - {item}")
        print("\nNotes:")
        for item in notes:
            print(f"  - {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
