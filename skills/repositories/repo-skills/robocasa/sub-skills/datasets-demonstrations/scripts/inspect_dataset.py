#!/usr/bin/env python3
"""Inspect a local RoboCasa LeRobot or legacy HDF5 dataset without networking.

The default inspection reads metadata and file structure only. Supplying
--sample-index additionally asks LeRobot 0.3.x to load one local sample while
forcing Hugging Face offline mode.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


class InspectionError(RuntimeError):
    """Raised for an actionable local dataset validation failure."""


def _read_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise InspectionError(f"cannot read JSON metadata {path}: {exc}") from exc


def _count_jsonl(path: Path) -> int | None:
    if not path.is_file():
        return None
    try:
        with path.open("r", encoding="utf-8") as stream:
            return sum(1 for line in stream if line.strip())
    except OSError as exc:
        raise InspectionError(f"cannot read JSONL metadata {path}: {exc}") from exc


def _shape_and_dtype(value: Any) -> dict[str, Any]:
    shape = getattr(value, "shape", None)
    dtype = getattr(value, "dtype", None)
    if shape is None and hasattr(value, "size") and callable(value.size):
        try:
            shape = tuple(value.size())
        except TypeError:
            shape = None
    return {
        "type": type(value).__name__,
        "shape": list(shape) if shape is not None else None,
        "dtype": str(dtype) if dtype is not None else None,
    }


def _sample_lerobot(root: Path, sample_index: int) -> dict[str, Any]:
    if sample_index < 0:
        raise InspectionError("--sample-index must be non-negative")

    # Refuse network fallback if the local dataset is incomplete. Override
    # inherited values so --sample-index is genuinely offline even when the
    # caller's shell exported a false-like setting.
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["HF_DATASETS_OFFLINE"] = "1"
    try:
        from lerobot.datasets.lerobot_dataset import LeRobotDataset
    except ImportError as exc:
        raise InspectionError(
            "LeRobot is unavailable; install RoboCasa's dataset dependencies "
            "before using --sample-index"
        ) from exc

    try:
        dataset = LeRobotDataset(repo_id="robocasa365", root=root)
        if sample_index >= len(dataset):
            raise InspectionError(
                f"sample index {sample_index} is outside dataset length {len(dataset)}"
            )
        sample = dataset[sample_index]
    except InspectionError:
        raise
    except Exception as exc:
        raise InspectionError(
            "LeRobot could not load the requested local sample in offline mode: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    return {
        "index": sample_index,
        "keys": {key: _shape_and_dtype(value) for key, value in sample.items()},
    }


def _inspect_lerobot(root: Path, sample_index: int | None) -> tuple[dict[str, Any], bool]:
    meta = root / "meta"
    info_path = meta / "info.json"
    info = _read_json(info_path) if info_path.is_file() else None

    parquet_files = sorted(root.glob("data/*/episode_*.parquet"))
    video_files = sorted(root.glob("videos/*/*/episode_*.mp4"))
    episode_dirs = sorted((root / "extras").glob("episode_*"))
    dataset_meta = root / "extras" / "dataset_meta.json"

    required_training = [
        info_path,
        meta / "tasks.jsonl",
        meta / "episodes.jsonl",
    ]
    missing_training = [str(path.relative_to(root)) for path in required_training if not path.is_file()]
    if not parquet_files:
        missing_training.append("data/*/episode_*.parquet")

    replay_missing = []
    if not dataset_meta.is_file():
        replay_missing.append("extras/dataset_meta.json")
    if not episode_dirs:
        replay_missing.append("extras/episode_*/")
    else:
        for episode_dir in episode_dirs:
            for name in ("ep_meta.json", "model.xml.gz", "states.npz"):
                path = episode_dir / name
                if not path.is_file():
                    replay_missing.append(str(path.relative_to(root)))

    result: dict[str, Any] = {
        "format": "lerobot",
        "root": str(root),
        "metadata": {
            "info": info,
            "tasks": _count_jsonl(meta / "tasks.jsonl"),
            "episodes": _count_jsonl(meta / "episodes.jsonl"),
            "episode_stats": _count_jsonl(meta / "episodes_stats.jsonl"),
            "has_stats": (meta / "stats.json").is_file(),
            "has_modality": (meta / "modality.json").is_file(),
            "has_embodiment": (meta / "embodiment.json").is_file(),
        },
        "files": {
            "parquet_episodes": len(parquet_files),
            "camera_videos": len(video_files),
            "replay_extra_episodes": len(episode_dirs),
        },
        "readiness": {
            "training_or_sample_access": not missing_training,
            "recorded_camera_video": bool(video_files),
            "replay_inputs": not replay_missing and not missing_training,
        },
        "missing": {
            "training_or_sample_access": missing_training,
            "replay_inputs": replay_missing,
        },
    }

    if sample_index is not None:
        if missing_training:
            raise InspectionError(
                "cannot load a sample: the LeRobot tree is incomplete; missing "
                + ", ".join(missing_training)
            )
        result["sample"] = _sample_lerobot(root, sample_index)

    complete = not missing_training
    return result, complete


def _decode_json_attr(value: Any) -> Any:
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value.item() if hasattr(value, "item") else value


def _inspect_hdf5(path: Path) -> tuple[dict[str, Any], bool]:
    try:
        import h5py
    except ImportError as exc:
        raise InspectionError("h5py is required to inspect a legacy HDF5 dataset") from exc

    try:
        with h5py.File(path, "r") as dataset:
            if "data" not in dataset:
                raise InspectionError("legacy HDF5 dataset is missing its top-level 'data' group")
            data = dataset["data"]
            episodes = sorted(data.keys())
            first_name = episodes[0] if episodes else None
            first = data[first_name] if first_name is not None else None

            first_datasets: dict[str, Any] = {}
            first_attrs: dict[str, Any] = {}
            if first is not None:
                for key, value in first.items():
                    if hasattr(value, "shape"):
                        first_datasets[key] = {
                            "shape": list(value.shape),
                            "dtype": str(value.dtype),
                        }
                    else:
                        first_datasets[key] = {"type": type(value).__name__}
                for key, value in first.attrs.items():
                    if key == "model_file":
                        first_attrs[key] = "present" if value else "empty"
                    else:
                        first_attrs[key] = _decode_json_attr(value)

            data_attrs = {
                key: _decode_json_attr(value) for key, value in data.attrs.items()
            }
            masks = sorted(dataset["mask"].keys()) if "mask" in dataset else []

            missing = []
            if not episodes:
                missing.append("data/demo_* episodes")
            if first is not None and "actions" not in first:
                missing.append(f"data/{first_name}/actions")

            replay_missing = []
            if first is not None:
                if "states" not in first:
                    replay_missing.append(f"data/{first_name}/states")
                if "model_file" not in first.attrs:
                    replay_missing.append(f"data/{first_name}.attrs['model_file']")
                if "env_args" not in data.attrs:
                    replay_missing.append("data.attrs['env_args']")

            result = {
                "format": "hdf5",
                "path": str(path),
                "metadata": {
                    "episodes": len(episodes),
                    "filter_masks": masks,
                    "data_attrs": data_attrs,
                    "first_episode": first_name,
                    "first_episode_datasets": first_datasets,
                    "first_episode_attrs": first_attrs,
                },
                "readiness": {
                    "trajectory_access": not missing,
                    "offline_observation_video": bool(first is not None and "obs" in first),
                    "replay_inputs": not replay_missing and not missing,
                },
                "missing": {
                    "trajectory_access": missing,
                    "replay_inputs": replay_missing,
                },
            }
    except InspectionError:
        raise
    except OSError as exc:
        raise InspectionError(f"cannot open HDF5 dataset {path}: {exc}") from exc

    return result, not missing


def _detect_format(path: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    if path.is_file() and path.suffix.lower() in {".h5", ".hdf5"}:
        return "hdf5"
    if path.is_dir() and (path / "meta").is_dir():
        return "lerobot"
    raise InspectionError(
        "cannot detect dataset format: expected an HDF5 file or a LeRobot root "
        "containing meta/"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect a local RoboCasa LeRobot or legacy HDF5 dataset without networking."
    )
    parser.add_argument("--dataset", required=True, type=Path, help="local dataset path")
    parser.add_argument(
        "--format",
        choices=("auto", "lerobot", "hdf5"),
        default="auto",
        help="dataset format; auto detects from the local path",
    )
    parser.add_argument(
        "--sample-index",
        type=int,
        default=None,
        help="optionally load one LeRobot sample in forced offline mode",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit compact JSON instead of indented JSON",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    path = args.dataset.expanduser().resolve()
    if not path.exists():
        print(
            f"ERROR: dataset path does not exist: {path}. Registry metadata does not download data.",
            file=sys.stderr,
        )
        return 2

    try:
        dataset_format = _detect_format(path, args.format)
        if dataset_format == "lerobot":
            if not path.is_dir():
                raise InspectionError("LeRobot --dataset must point to a directory")
            result, complete = _inspect_lerobot(path, args.sample_index)
        else:
            if args.sample_index is not None:
                raise InspectionError("--sample-index is only available for LeRobot datasets")
            if not path.is_file():
                raise InspectionError("HDF5 --dataset must point to a file")
            result, complete = _inspect_hdf5(path)
    except InspectionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=None if args.json else 2, sort_keys=True, default=str))
    if not complete:
        print(
            "ERROR: local dataset exists but is incomplete for trajectory access; see the missing fields above.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
