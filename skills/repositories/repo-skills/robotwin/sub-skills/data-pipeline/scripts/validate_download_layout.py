#!/usr/bin/env python3
"""Validate a normalized RoboTwin download or collection tree.

The checker is read-only and self-contained. It validates the normalized
`data/<task_config>/<task>/<embodiment>/` layout, checks episode numbering,
confirms the paired sidecar directories, and samples one or more HDF5 files for
basic XPolicyLab schema sanity.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import h5py

EPISODE_RE = re.compile(r"^episode_(\d{7})\.hdf5$")
VIDEO_RE = re.compile(r"^episode_(\d{7})\.mp4$")
INSTRUCTION_RE = re.compile(r"^episode_(\d{7})\.json$")
REQUIRED_GROUPS = ("state", "action", "vision", "additional_info")
EXPECTED_CAMERA_GROUPS = (
    "cam_head",
    "cam_left_wrist",
    "cam_right_wrist",
    "cam_third_view",
)


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


def _group_lengths(group: h5py.Group | None) -> dict[str, int]:
    if group is None:
        return {}
    lengths: dict[str, int] = {}
    for name, node in group.items():
        if isinstance(node, h5py.Dataset) and node.shape not in (None, ()):  # type: ignore[comparison-overlap]
            lengths[name] = int(node.shape[0])
    return lengths


def _common_length(values: list[int]) -> int | None:
    unique = sorted(set(values))
    if len(unique) == 1:
        return unique[0]
    return None


def _inspect_episode(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        with h5py.File(path, "r") as handle:
            attrs = {str(key): _decode_scalar(value) for key, value in handle.attrs.items()}
            if attrs.get("source_format") != "RoboTwin":
                issues.append("source_format attr is missing or not RoboTwin")

            if "data_format_version" not in handle:
                issues.append("missing dataset: data_format_version")
            else:
                try:
                    version = _decode_scalar(handle["data_format_version"][()])
                    if str(version) != "v1.0":
                        issues.append(f"unexpected data_format_version: {version}")
                except Exception:
                    issues.append("data_format_version is not readable")

            if "instructions" not in handle:
                issues.append("missing dataset: instructions")

            for group_name in REQUIRED_GROUPS:
                if group_name not in handle:
                    issues.append(f"missing top-level group: {group_name}")

            state_group = handle["state"] if "state" in handle else None
            action_group = handle["action"] if "action" in handle else None
            vision_group = handle["vision"] if "vision" in handle else None

            state_lengths = _group_lengths(state_group)
            action_lengths = _group_lengths(action_group)
            if not state_lengths:
                issues.append("state group has no datasets")
            if not action_lengths:
                issues.append("action group has no datasets")

            state_horizon = _common_length(list(state_lengths.values())) if state_lengths else None
            action_horizon = _common_length(list(action_lengths.values())) if action_lengths else None
            if state_horizon is None and state_lengths:
                issues.append("state group has mixed lengths")
            if action_horizon is None and action_lengths:
                issues.append("action group has mixed lengths")
            if state_horizon is not None and action_horizon is not None and state_horizon != action_horizon:
                issues.append(f"state/action horizon mismatch: {state_horizon} vs {action_horizon}")

            if vision_group is None:
                issues.append("missing top-level group: vision")
            else:
                camera_lengths: list[int] = []
                for camera_name, camera_group in vision_group.items():
                    if not isinstance(camera_group, h5py.Group):
                        continue
                    if "colors" not in camera_group:
                        issues.append(f"vision/{camera_name} is missing colors")
                        continue
                    if "shape" not in camera_group:
                        issues.append(f"vision/{camera_name} is missing shape")
                    camera_lengths.append(int(camera_group["colors"].shape[0]))
                if not camera_lengths:
                    issues.append("vision group has no camera datasets")
                else:
                    vision_horizon = _common_length(camera_lengths)
                    if vision_horizon is None:
                        issues.append("vision cameras have mixed lengths")
                    else:
                        candidate = state_horizon if state_horizon is not None else action_horizon
                        if candidate is not None and vision_horizon != candidate:
                            issues.append(f"vision horizon mismatch: {vision_horizon} vs {candidate}")

                present_cameras = [name for name, node in vision_group.items() if isinstance(node, h5py.Group)]
                if not any(name in present_cameras for name in EXPECTED_CAMERA_GROUPS):
                    issues.append("no expected camera groups found in vision")

            if state_horizon is not None and state_horizon <= 0:
                issues.append("state horizon is not positive")
            if action_horizon is not None and action_horizon <= 0:
                issues.append("action horizon is not positive")
    except Exception as exc:  # pragma: no cover - surfaced in CLI output
        issues.append(f"failed to open file: {exc}")
    return issues


def _parse_sidecar_index(path: Path, regex: re.Pattern[str]) -> int | None:
    match = regex.match(path.name)
    if not match:
        return None
    return int(match.group(1))


def _collect_sidecars(directory: Path, regex: re.Pattern[str]) -> tuple[list[Path], list[str]]:
    files = [path for path in sorted(directory.iterdir()) if path.is_file()]
    issues: list[str] = []
    normalized: list[tuple[int, Path]] = []
    for path in files:
        index = _parse_sidecar_index(path, regex)
        if index is None:
            issues.append(f"unexpected sidecar name: {path.name}")
            continue
        normalized.append((index, path))
    normalized.sort(key=lambda item: item[0])
    return [path for _, path in normalized], issues


def _validate_task_directory(
    task_dir: Path,
    embodiment: str,
    inspect_samples: int,
    inspect_all: bool,
    require_sidecar_files: bool,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    embodiment_dir = task_dir / embodiment
    data_dir = embodiment_dir / "data"
    video_dir = embodiment_dir / "video"
    instruction_dir = embodiment_dir / "instruction"

    if not data_dir.is_dir():
        errors.append(f"missing data directory: {data_dir}")
        return errors, warnings
    if not video_dir.is_dir():
        errors.append(f"missing sidecar directory: {video_dir}")
    if not instruction_dir.is_dir():
        errors.append(f"missing sidecar directory: {instruction_dir}")

    all_episode_files = sorted(
        path
        for path in data_dir.iterdir()
        if path.is_file() and path.suffix in {".hdf5", ".h5"} and path.name.startswith("episode")
    )
    normalized_files = [path for path in all_episode_files if EPISODE_RE.match(path.name)]
    legacy_names = [path for path in all_episode_files if path not in normalized_files]

    if legacy_names:
        errors.append(
            "non-normalized episode names found: "
            + ", ".join(path.name for path in legacy_names[:5])
        )
    if not normalized_files:
        errors.append(f"no normalized episode_*.hdf5 files found in {data_dir}")
        return errors, warnings

    indices = [int(EPISODE_RE.match(path.name).group(1)) for path in normalized_files]
    if indices != list(range(len(indices))):
        errors.append(
            f"episode numbering is not contiguous from 0000000: {indices[:10]}"
        )

    if video_dir.is_dir():
        video_files, video_issues = _collect_sidecars(video_dir, VIDEO_RE)
        errors.extend(f"video sidecar: {issue}" for issue in video_issues)
        if not video_files:
            message = f"no video sidecars found in {video_dir}"
            if require_sidecar_files:
                errors.append(message)
            else:
                warnings.append(message)
        elif len(video_files) != len(normalized_files):
            errors.append(
                f"video count mismatch: {len(video_files)} videos vs {len(normalized_files)} episodes"
            )
        else:
            video_indices = [_parse_sidecar_index(path, VIDEO_RE) for path in video_files]
            if video_indices != indices:
                errors.append("video numbering does not match the HDF5 episodes")

    if instruction_dir.is_dir():
        instruction_files, instruction_issues = _collect_sidecars(instruction_dir, INSTRUCTION_RE)
        errors.extend(f"instruction sidecar: {issue}" for issue in instruction_issues)
        if not instruction_files:
            message = f"no instruction sidecars found in {instruction_dir}"
            if require_sidecar_files:
                errors.append(message)
            else:
                warnings.append(message)
        elif len(instruction_files) != len(normalized_files):
            errors.append(
                f"instruction count mismatch: {len(instruction_files)} instructions vs {len(normalized_files)} episodes"
            )
        else:
            instruction_indices = [_parse_sidecar_index(path, INSTRUCTION_RE) for path in instruction_files]
            if instruction_indices != indices:
                errors.append("instruction numbering does not match the HDF5 episodes")

    seed_file = embodiment_dir / "seed.txt"
    if seed_file.exists():
        try:
            tokens = seed_file.read_text(encoding="utf-8").split()
            [int(token) for token in tokens]
        except Exception as exc:
            errors.append(f"seed.txt is not readable as integers: {exc}")
    else:
        warnings.append(f"missing optional file: {seed_file}")

    scene_info = embodiment_dir / "scene_info.json"
    if scene_info.exists():
        try:
            json.loads(scene_info.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"scene_info.json is not valid JSON: {exc}")
    else:
        warnings.append(f"missing optional file: {scene_info}")

    samples = normalized_files if inspect_all else normalized_files[: max(1, inspect_samples)]
    for sample in samples:
        sample_issues = _inspect_episode(sample)
        if sample_issues:
            errors.append(f"{sample.name}: " + "; ".join(sample_issues))

    return errors, warnings


def _discover_task_directories(
    root: Path,
    task_config: str | None,
    task: str | None,
    embodiment: str,
) -> list[tuple[str, Path]]:
    root = root.expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(root)

    if task_config:
        if root.name == task_config and any(
            (child / embodiment / "data").is_dir()
            for child in root.iterdir()
            if child.is_dir()
        ):
            cfg_dirs = [root]
        else:
            cfg_dir = root / task_config
            if not cfg_dir.is_dir():
                raise FileNotFoundError(cfg_dir)
            cfg_dirs = [cfg_dir]
    else:
        if any(
            (child / embodiment / "data").is_dir()
            for child in root.iterdir()
            if child.is_dir()
        ):
            cfg_dirs = [root]
        else:
            cfg_dirs = [child for child in sorted(root.iterdir()) if child.is_dir()]

    discovered: list[tuple[str, Path]] = []
    for cfg_dir in cfg_dirs:
        task_dirs = [
            child
            for child in sorted(cfg_dir.iterdir())
            if child.is_dir() and (child / embodiment / "data").is_dir()
        ]
        for task_dir in task_dirs:
            if task and task_dir.name != task:
                continue
            discovered.append((cfg_dir.name, task_dir))
    return discovered


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate normalized RoboTwin download and collection layouts."
    )
    parser.add_argument("root", type=Path, help="Data root or task-config root to validate.")
    parser.add_argument("--task-config", help="Restrict validation to a single task_config directory.")
    parser.add_argument("--task", help="Restrict validation to a single task directory.")
    parser.add_argument(
        "--embodiment",
        default="aloha_agilex",
        help="Embodiment directory name to validate. Default: aloha_agilex.",
    )
    parser.add_argument(
        "--inspect-samples",
        type=int,
        default=1,
        help="Number of episode files to inspect per task when --inspect-all is not used.",
    )
    parser.add_argument(
        "--inspect-all",
        action="store_true",
        help="Inspect every episode file instead of sampling.",
    )
    parser.add_argument(
        "--require-sidecar-files",
        action="store_true",
        help="Fail if video/instruction sidecar directories are empty.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if args.inspect_samples <= 0:
        raise SystemExit("--inspect-samples must be positive")

    targets = _discover_task_directories(args.root, args.task_config, args.task, args.embodiment)
    if not targets:
        raise SystemExit("No normalized task directories found under the supplied root.")

    total_errors = 0
    total_warnings = 0
    for index, (cfg_name, task_dir) in enumerate(targets):
        errors, warnings = _validate_task_directory(
            task_dir,
            args.embodiment,
            args.inspect_samples,
            args.inspect_all,
            args.require_sidecar_files,
        )
        total_errors += len(errors)
        total_warnings += len(warnings)

        print(f"[task] {cfg_name}/{task_dir.name}/{args.embodiment}")
        if errors:
            print("  errors:")
            for issue in errors:
                print(f"    - {issue}")
        else:
            data_count = len(
                [
                    path
                    for path in (task_dir / args.embodiment / "data").iterdir()
                    if path.is_file() and EPISODE_RE.match(path.name)
                ]
            )
            print(f"  data episodes: {data_count}")
            print("  status: ok")

        if warnings:
            print("  warnings:")
            for warning in warnings:
                print(f"    - {warning}")

        if index + 1 < len(targets):
            print()

    print(f"summary: {len(targets)} task directory(s), {total_errors} fatal issue(s), {total_warnings} warning(s)")
    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
