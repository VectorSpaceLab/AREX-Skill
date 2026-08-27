#!/usr/bin/env python3
"""Inspect RoboTwin and XPolicyLab HDF5 episodes.

This script is read-only and self-contained. It summarizes one HDF5 file or a
small set of files found under a directory, detects whether the layout looks
like normalized XPolicyLab data or an older legacy raw episode bundle, and
reports the most common structural signals used by the data pipeline.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import h5py

EXPECTED_XPOLICYLAB_GROUPS = ("state", "action", "vision", "additional_info")
EXPECTED_CAMERA_GROUPS = (
    "cam_head",
    "cam_left_wrist",
    "cam_right_wrist",
    "cam_third_view",
)
LEGACY_RAW_GROUPS = ("joint_action", "observation")


def _decode_scalar(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if hasattr(value, "item"):
        try:
            scalar = value.item()
        except Exception:
            return value
        if isinstance(scalar, bytes):
            return scalar.decode("utf-8", errors="replace")
        return scalar
    return value


def _preview(value: Any, limit: int = 120) -> str:
    text = str(_decode_scalar(value))
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _shape_text(shape: tuple[int, ...] | None) -> str:
    if shape is None:
        return "?"
    if shape == ():
        return "scalar"
    return "(" + ", ".join(str(dim) for dim in shape) + ")"


def _dataset_info(dataset: h5py.Dataset) -> dict[str, Any]:
    info: dict[str, Any] = {
        "shape": list(dataset.shape) if dataset.shape is not None else None,
        "dtype": str(dataset.dtype),
    }
    if dataset.shape == ():
        try:
            info["value"] = _preview(dataset[()])
        except Exception:
            pass
    elif dataset.size and dataset.size <= 4 and dataset.dtype.kind in {"S", "O", "U"}:
        try:
            info["sample"] = _preview(dataset[()])
        except Exception:
            pass
    return info


def _length(dataset: h5py.Dataset) -> int | None:
    if dataset.shape is None or dataset.shape == ():
        return None
    return int(dataset.shape[0])


def _group_lengths(group: h5py.Group | None) -> dict[str, int]:
    if group is None:
        return {}
    lengths: dict[str, int] = {}
    for name, node in group.items():
        if isinstance(node, h5py.Dataset):
            length = _length(node)
            if length is not None:
                lengths[name] = length
    return lengths


def _common_length(lengths: list[int]) -> int | None:
    unique = sorted(set(lengths))
    if len(unique) == 1:
        return unique[0]
    return None


def _select_files(paths: list[Path], limit: int) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for raw_path in paths:
        path = raw_path.expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(path)
        if path.is_file():
            candidates = [path]
        else:
            candidates = sorted(
                {
                    *path.rglob("*.hdf5"),
                    *path.rglob("*.h5"),
                }
            )
        for candidate in candidates:
            if candidate in seen:
                continue
            files.append(candidate)
            seen.add(candidate)
            if limit > 0 and len(files) >= limit:
                return files
    return files


def _classify_format(top_level_keys: list[str]) -> str:
    if all(key in top_level_keys for key in EXPECTED_XPOLICYLAB_GROUPS):
        return "xpolicylab"
    if any(key in top_level_keys for key in LEGACY_RAW_GROUPS):
        return "legacy-raw"
    return "unknown"


def _summarize_camera_group(camera_group: h5py.Group) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for name, node in camera_group.items():
        if isinstance(node, h5py.Dataset):
            summary[name] = _dataset_info(node)
    return summary


def _summarize_xpolicylab_file(path: Path) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "path": str(path),
        "format": "unknown",
        "attrs": {},
        "top_level_keys": [],
        "frequency": None,
        "instruction": None,
        "instruction_count": None,
        "horizon": None,
        "state": {},
        "action": {},
        "vision": {},
        "issues": [],
    }

    try:
        with h5py.File(path, "r") as handle:
            summary["attrs"] = {
                str(key): _decode_scalar(value)
                for key, value in handle.attrs.items()
            }
            top_level_keys = sorted(handle.keys())
            summary["top_level_keys"] = top_level_keys
            layout = _classify_format(top_level_keys)
            summary["format"] = layout

            if layout == "xpolicylab":
                for key in EXPECTED_XPOLICYLAB_GROUPS:
                    if key not in handle:
                        summary["issues"].append(f"missing top-level group: {key}")

                if "additional_info" in handle:
                    additional_info = handle["additional_info"]
                    if "frequency" in additional_info:
                        try:
                            summary["frequency"] = int(_decode_scalar(additional_info["frequency"][()]))
                        except Exception:
                            summary["issues"].append("additional_info/frequency is not readable")
                    else:
                        summary["issues"].append("missing dataset: additional_info/frequency")

                if "instruction" in handle:
                    try:
                        summary["instruction"] = _preview(handle["instruction"][()])
                    except Exception:
                        summary["issues"].append("instruction dataset is not readable")

                if "instructions" in handle:
                    instructions_node = handle["instructions"]
                    if isinstance(instructions_node, h5py.Dataset):
                        if instructions_node.shape == ():
                            try:
                                decoded = _decode_scalar(instructions_node[()])
                                try:
                                    parsed = json.loads(str(decoded))
                                    if isinstance(parsed, list):
                                        summary["instruction_count"] = len(parsed)
                                    else:
                                        summary["instruction_count"] = 1
                                except Exception:
                                    summary["instruction_count"] = 1
                            except Exception:
                                pass
                        else:
                            summary["instruction_count"] = int(instructions_node.shape[0])
                else:
                    summary["issues"].append("missing dataset: instructions")

                state_group = handle["state"] if "state" in handle else None
                action_group = handle["action"] if "action" in handle else None
                vision_group = handle["vision"] if "vision" in handle else None

                summary["state"] = {
                    name: _dataset_info(node)
                    for name, node in (state_group.items() if state_group is not None else [])
                    if isinstance(node, h5py.Dataset)
                }
                summary["action"] = {
                    name: _dataset_info(node)
                    for name, node in (action_group.items() if action_group is not None else [])
                    if isinstance(node, h5py.Dataset)
                }

                state_lengths = _group_lengths(state_group)
                action_lengths = _group_lengths(action_group)
                state_horizon = _common_length(list(state_lengths.values())) if state_lengths else None
                action_horizon = _common_length(list(action_lengths.values())) if action_lengths else None
                if state_horizon is None:
                    summary["issues"].append("state group is empty or has mixed lengths")
                if action_horizon is None:
                    summary["issues"].append("action group is empty or has mixed lengths")
                if state_horizon is not None and action_horizon is not None and state_horizon != action_horizon:
                    summary["issues"].append(
                        f"state/action horizon mismatch: {state_horizon} vs {action_horizon}"
                    )
                horizon = state_horizon if state_horizon is not None else action_horizon

                if vision_group is not None:
                    for camera_name, camera_group in vision_group.items():
                        if isinstance(camera_group, h5py.Group):
                            summary["vision"][camera_name] = _summarize_camera_group(camera_group)
                    camera_lengths: list[int] = []
                    for camera_name, camera_group in vision_group.items():
                        if not isinstance(camera_group, h5py.Group):
                            continue
                        if "colors" not in camera_group:
                            summary["issues"].append(f"vision/{camera_name} is missing colors")
                            continue
                        camera_lengths.append(int(camera_group["colors"].shape[0]))
                    if camera_lengths:
                        vision_horizon = _common_length(camera_lengths)
                        if vision_horizon is None:
                            summary["issues"].append("vision cameras have mixed lengths")
                        elif horizon is not None and vision_horizon != horizon:
                            summary["issues"].append(
                                f"vision horizon mismatch: {vision_horizon} vs {horizon}"
                            )
                        else:
                            horizon = vision_horizon if horizon is None else horizon
                    else:
                        summary["issues"].append("vision group has no camera datasets")
                else:
                    summary["issues"].append("missing top-level group: vision")

                summary["horizon"] = horizon
                if horizon is None:
                    summary["issues"].append("could not infer a consistent horizon")

                if "state" not in handle or not summary["state"]:
                    summary["issues"].append("state group has no datasets")
                if "action" not in handle or not summary["action"]:
                    summary["issues"].append("action group has no datasets")
                if "vision" not in handle:
                    summary["issues"].append("vision group missing entirely")

            elif layout == "legacy-raw":
                summary["issues"].append(
                    "legacy raw layout detected; convert it with the legacy conversion workflow"
                )
            else:
                summary["issues"].append("unrecognized HDF5 layout")
    except Exception as exc:  # pragma: no cover - surfaced in CLI output
        summary["issues"].append(f"failed to open file: {exc}")

    return summary


def _print_human(summary: dict[str, Any]) -> None:
    status = "ok" if not summary["issues"] else "warn"
    print(f"[{status}] {summary['path']}")
    print(f"  format: {summary['format']}")
    if summary["attrs"]:
        attrs = summary["attrs"]
        interesting = [
            f"{key}={attrs[key]}"
            for key in ("source_format", "source_path", "data_format_version")
            if key in attrs
        ]
        if interesting:
            print("  attrs: " + ", ".join(interesting))
    if summary["frequency"] is not None:
        print(f"  frequency: {summary['frequency']}")
    if summary["instruction"] is not None:
        print(f"  instruction: {summary['instruction']}")
    if summary["instruction_count"] is not None:
        print(f"  instructions: {summary['instruction_count']}")
    if summary["horizon"] is not None:
        print(f"  horizon: {summary['horizon']}")

    if summary["state"]:
        pieces = []
        for name, info in summary["state"].items():
            shape = tuple(info["shape"]) if info["shape"] is not None else None
            pieces.append(f"{name}{_shape_text(shape)}")
        print("  state: " + ", ".join(pieces))
    if summary["action"]:
        pieces = []
        for name, info in summary["action"].items():
            shape = tuple(info["shape"]) if info["shape"] is not None else None
            pieces.append(f"{name}{_shape_text(shape)}")
        print("  action: " + ", ".join(pieces))
    if summary["vision"]:
        pieces = []
        for camera_name, camera in summary["vision"].items():
            colors = camera.get("colors", {})
            shape = tuple(colors["shape"]) if colors.get("shape") is not None else None
            pieces.append(f"{camera_name}/colors{_shape_text(shape)}")
        print("  vision: " + ", ".join(pieces))

    if summary["issues"]:
        print("  issues:")
        for issue in summary["issues"]:
            print(f"    - {issue}")
    else:
        print("  issues: none")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect RoboTwin or XPolicyLab HDF5 episodes without importing repository code."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="One or more HDF5 files or directories to inspect.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of files to inspect per directory input. Use 0 for no limit.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a human summary.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with a failure code when any issue is detected.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    files = _select_files(args.paths, args.limit)
    if not files:
        raise SystemExit("No HDF5 files found in the supplied path(s).")

    summaries = [_summarize_xpolicylab_file(path) for path in files]

    if args.json:
        print(json.dumps({"files": summaries}, indent=2, ensure_ascii=False))
    else:
        for index, summary in enumerate(summaries):
            if index:
                print()
            _print_human(summary)

    if args.strict and any(summary["issues"] for summary in summaries):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
