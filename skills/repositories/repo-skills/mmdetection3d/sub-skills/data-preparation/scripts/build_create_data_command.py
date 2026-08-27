#!/usr/bin/env python3
"""Render MMDetection3D data-preparation commands without executing them.

This helper is intentionally safe: it prints commands for a human or agent to
review. It does not import MMDetection3D, download datasets, convert data,
modify pickles, or touch the filesystem except for normal stdout/stderr.
"""

from __future__ import annotations

import argparse
import json
import shlex
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence


CREATE_DATASETS = {
    "kitti",
    "waymo",
    "nuscenes",
    "lyft",
    "semantickitti",
    "s3dis",
    "scannet",
    "sunrgbd",
}
UPDATE_INFO_DATASETS = {
    "kitti",
    "waymo",
    "scannet",
    "sunrgbd",
    "lyft",
    "nuscenes",
    "s3dis",
}
UPDATE_COORD_DATASETS = {
    "kitti",
    "nuscenes",
    "lyft",
    "waymo",
    "scannet",
    "s3dis",
    "sunrgbd",
}


@dataclass(frozen=True)
class DatasetDefaults:
    root: str
    out_dir: str
    extra_tag: str
    version: str | None = None
    max_sweeps: int | None = None
    workers: int | None = None


DEFAULTS: Dict[str, DatasetDefaults] = {
    "kitti": DatasetDefaults("data/kitti", "data/kitti", "kitti", "v1.0"),
    "waymo": DatasetDefaults("data/waymo", "data/waymo", "waymo", "v1.4", 10, 4),
    "nuscenes": DatasetDefaults("data/nuscenes", "data/nuscenes", "nuscenes", "v1.0", 10),
    "lyft": DatasetDefaults("data/lyft", "data/lyft", "lyft", "v1.01", 10),
    "semantickitti": DatasetDefaults("data/semantickitti", "data/semantickitti", "semantickitti"),
    "s3dis": DatasetDefaults("data/s3dis", "data/s3dis", "s3dis", workers=4),
    "scannet": DatasetDefaults("data/scannet", "data/scannet", "scannet", workers=4),
    "sunrgbd": DatasetDefaults("data/sunrgbd", "data/sunrgbd", "sunrgbd", workers=4),
}


DATASET_NOTES = {
    "kitti": "supports --with-plane when training/planes exists and --only-gt-database for ready-made info pickles",
    "waymo": "converts TFRecords into kitti_format; tune --workers and consider --quiet-tf",
    "nuscenes": "use --version v1.0 or v1.0-mini; --only-gt-database requires existing infos",
    "lyft": "use --include-lyft-fixer to render the standard post-conversion fixer command",
    "semantickitti": "generates train/val/test segmentation infos from sequences/",
    "s3dis": "requires dataset-provided S3DIS export output before running create_data.py",
    "scannet": "requires ScanNet batch export output before running create_data.py",
    "sunrgbd": "requires MATLAB-extracted sunrgbd_trainval before running create_data.py",
    "custom": "layout/schema guidance only in v1.4.0; the inspected dispatcher has no verified custom branch",
}


def shell_join(parts: Sequence[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def command_with_env(parts: Sequence[str], env: Dict[str, str] | None = None) -> str:
    if not env:
        return shell_join(parts)
    env_prefix = " ".join(f"{key}={shlex.quote(value)}" for key, value in env.items())
    return f"{env_prefix} {shell_join(parts)}"


def maybe_add(parts: List[str], flag: str, value) -> None:
    if value is not None:
        parts.extend([flag, str(value)])


def render_create_data(args: argparse.Namespace) -> Dict[str, object]:
    dataset = args.dataset.lower()
    if dataset not in CREATE_DATASETS:
        raise SystemExit(f"Unsupported create-data dataset: {dataset}")

    defaults = DEFAULTS[dataset]
    root_path = args.root_path or defaults.root
    out_dir = args.out_dir or defaults.out_dir
    extra_tag = args.extra_tag or defaults.extra_tag
    version = args.version if args.version is not None else defaults.version
    max_sweeps = args.max_sweeps if args.max_sweeps is not None else defaults.max_sweeps
    workers = args.workers if args.workers is not None else defaults.workers

    cmd: List[str] = [
        args.python,
        "tools/create_data.py",
        dataset,
        "--root-path",
        root_path,
        "--out-dir",
        out_dir,
        "--extra-tag",
        extra_tag,
    ]

    if version is not None and dataset in {"kitti", "waymo", "nuscenes", "lyft"}:
        maybe_add(cmd, "--version", version)
    if max_sweeps is not None and dataset in {"waymo", "nuscenes", "lyft"}:
        maybe_add(cmd, "--max-sweeps", max_sweeps)
    if workers is not None and dataset in {"waymo", "s3dis", "scannet", "sunrgbd"}:
        maybe_add(cmd, "--workers", workers)

    warnings: List[str] = [
        "Rendered only; this helper did not run conversion or check that inputs exist.",
        "Run native conversion only from a MMDetection3D checkout that contains tools/create_data.py.",
    ]

    if args.with_plane:
        if dataset != "kitti":
            raise SystemExit("--with-plane is only valid for kitti")
        cmd.append("--with-plane")
    if args.only_gt_database:
        if dataset not in {"kitti", "waymo", "nuscenes"}:
            raise SystemExit("--only-gt-database is only supported for kitti, waymo, or nuscenes in this helper")
        cmd.append("--only-gt-database")
        warnings.append("Only-gtdb mode assumes the relevant train info pickle already exists.")
    if args.skip_cam_instances_infos:
        if dataset != "waymo":
            raise SystemExit("--skip-cam_instances-infos is only valid for waymo")
        cmd.append("--skip-cam_instances-infos")
    if args.skip_saving_sensor_data:
        if dataset != "waymo":
            raise SystemExit("--skip-saving-sensor-data is only valid for waymo")
        cmd.append("--skip-saving-sensor-data")
        warnings.append("Skipping sensor-data saving is safe only when compatible image/lidar outputs already exist or are not needed.")

    env = {"TF_CPP_MIN_LOG_LEVEL": "3"} if args.quiet_tf and dataset == "waymo" else None
    if args.quiet_tf and dataset != "waymo":
        warnings.append("--quiet-tf only affects waymo; no environment prefix was added for this dataset.")

    commands = [command_with_env(cmd, env)]

    if args.include_lyft_fixer:
        if dataset != "lyft":
            raise SystemExit("--include-lyft-fixer is only valid for lyft")
        fixer_version = version or "v1.01"
        commands.append(
            shell_join([
                args.python,
                "tools/dataset_converters/lyft_data_fixer.py",
                "--version",
                fixer_version,
                "--root-folder",
                root_path,
            ])
        )
        warnings.append("The Lyft fixer is a post-conversion command for the known corrupted lidar file.")

    if dataset == "waymo" and workers is not None and int(workers) > 32:
        warnings.append("Very high Waymo worker counts can exhaust CPU RAM or hang; reduce workers if conversion stalls.")
    if out_dir != root_path:
        warnings.append("Because --out-dir differs from --root-path, update configs or link converted outputs back to the expected dataset root.")

    return {
        "mode": "create-data",
        "dataset": dataset,
        "commands": commands,
        "warnings": warnings,
    }


def render_update_infos(args: argparse.Namespace) -> Dict[str, object]:
    dataset = args.dataset.lower()
    if dataset not in UPDATE_INFO_DATASETS:
        raise SystemExit(f"Unsupported update-infos dataset: {dataset}")
    cmd = [
        args.python,
        "tools/dataset_converters/update_infos_to_v2.py",
        "--dataset",
        dataset,
        "--pkl-path",
        args.pkl_path,
        "--out-dir",
        args.out_dir,
    ]
    warnings = [
        "Rendered only; this helper did not read or modify the pickle.",
        "Use a separate --out-dir first, then inspect the migrated info file before replacing originals.",
    ]
    return {"mode": "update-infos", "dataset": dataset, "commands": [shell_join(cmd)], "warnings": warnings}


def render_update_coords(args: argparse.Namespace) -> Dict[str, object]:
    dataset = args.dataset.lower()
    if dataset not in UPDATE_COORD_DATASETS:
        raise SystemExit(f"Unsupported update-coords dataset: {dataset}")
    cmd = [
        args.python,
        "tools/update_data_coords.py",
        dataset,
        "--root-dir",
        args.root_dir,
        "--version",
        args.version,
        "--out-dir",
        args.out_dir,
    ]
    warnings = [
        "Rendered only; this helper did not read or modify any pickle.",
        "Coordinate-update commands are for old coordinate-refactor files; back up data and prefer a separate --out-dir.",
    ]
    if args.out_dir == args.root_dir:
        warnings.append("The rendered command may overwrite files because --out-dir equals --root-dir.")
    if dataset in {"scannet", "s3dis"}:
        warnings.append("The native coordinate-update helper has no effective update for this dataset in v1.4.0.")
    return {"mode": "update-coords", "dataset": dataset, "commands": [shell_join(cmd)], "warnings": warnings}


def print_result(result: Dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    print("# Commands rendered only; review before running.")
    for warning in result.get("warnings", []):
        print(f"# WARNING: {warning}")
    for command in result.get("commands", []):
        print(command)


def print_dataset_list() -> None:
    print("Supported create-data datasets:")
    for name in sorted(CREATE_DATASETS):
        defaults = DEFAULTS[name]
        version = f", version={defaults.version}" if defaults.version else ""
        print(f"  - {name}: root={defaults.root}, tag={defaults.extra_tag}{version}; {DATASET_NOTES[name]}")
    print("\nCustom datasets:")
    print(f"  - custom: {DATASET_NOTES['custom']}")
    print("\nSupported update-infos datasets:")
    print("  - " + ", ".join(sorted(UPDATE_INFO_DATASETS)))
    print("\nSupported update-coords datasets:")
    print("  - " + ", ".join(sorted(UPDATE_COORD_DATASETS)))


def add_common_python(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--python", default="python", help="Python command to render; default: python")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Print structured JSON instead of shell text")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-datasets", help="List datasets supported by this renderer")
    list_parser.set_defaults(func=lambda _args: print_dataset_list())

    create = subparsers.add_parser("create-data", help="Render a tools/create_data.py command")
    create.add_argument("dataset", choices=sorted(CREATE_DATASETS), help="Dataset argument for create_data.py")
    create.add_argument("--root-path", help="Dataset root path to render")
    create.add_argument("--out-dir", help="Output directory to render")
    create.add_argument("--extra-tag", help="Info-file prefix/tag to render")
    create.add_argument("--version", help="Dataset version to render")
    create.add_argument("--max-sweeps", type=int, help="Lidar sweeps per example for Waymo/NuScenes/Lyft")
    create.add_argument("--workers", type=int, help="Worker count for Waymo/indoor converters")
    create.add_argument("--with-plane", action="store_true", help="Render KITTI plane-aware conversion flag")
    create.add_argument("--only-gt-database", action="store_true", help="Render only ground-truth database generation where supported")
    create.add_argument("--skip-cam_instances-infos", action="store_true", help="Render Waymo cam_instances skip flag")
    create.add_argument("--skip-saving-sensor-data", action="store_true", help="Render Waymo sensor-data saving skip flag")
    create.add_argument("--quiet-tf", action="store_true", help="Render TF_CPP_MIN_LOG_LEVEL=3 for Waymo")
    create.add_argument("--include-lyft-fixer", action="store_true", help="Also render the Lyft post-conversion data fixer command")
    add_common_python(create)
    create.set_defaults(func=lambda args: print_result(render_create_data(args), args.as_json))

    update_infos = subparsers.add_parser("update-infos", help="Render update_infos_to_v2.py command")
    update_infos.add_argument("--dataset", required=True, choices=sorted(UPDATE_INFO_DATASETS))
    update_infos.add_argument("--pkl-path", required=True, help="Info pickle to migrate")
    update_infos.add_argument("--out-dir", required=True, help="Directory for migrated output")
    add_common_python(update_infos)
    update_infos.set_defaults(func=lambda args: print_result(render_update_infos(args), args.as_json))

    update_coords = subparsers.add_parser("update-coords", help="Render update_data_coords.py command")
    update_coords.add_argument("--dataset", required=True, choices=sorted(UPDATE_COORD_DATASETS))
    update_coords.add_argument("--root-dir", required=True, help="Root directory containing old coordinate pickles")
    update_coords.add_argument("--out-dir", required=True, help="Output directory for updated pickles")
    update_coords.add_argument("--version", default="v1.0", help="Dataset version for coordinate update")
    add_common_python(update_coords)
    update_coords.set_defaults(func=lambda args: print_result(render_update_coords(args), args.as_json))

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
