#!/usr/bin/env python3
"""Print a JSON summary for a DeepLabCut project root or config file.

This script is read-only. It never creates, edits, or deletes files.

Usage:
    python summarize_dlc_project.py /path/to/project-or-config [--indent 2]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

KNOWN_LAYOUT_DIRS = (
    "videos",
    "labeled-data",
    "training-datasets",
    "dlc-models",
    "dlc-models-pytorch",
    "calibration_images",
    "camera_matrix",
    "corners",
    "undistortion",
)


def jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(item) for item in value]
    return value


def safe_str_path(value: Any) -> str | None:
    if value in (None, ""):
        return None
    try:
        return str(Path(value))
    except TypeError:
        return str(value)


def list_directory(path: Path, limit: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "exists": path.exists(),
        "kind": "missing",
        "count": 0,
        "sample": [],
    }
    if not path.exists():
        return result

    if path.is_dir():
        result["kind"] = "directory"
        try:
            entries = sorted(child.name for child in path.iterdir())
        except OSError as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
            return result
        result["count"] = len(entries)
        result["sample"] = entries[:limit]
        result["truncated"] = len(entries) > limit
        return result

    result["kind"] = "file"
    result["count"] = 1
    result["sample"] = [path.name]
    return result


def detect_project_type(cfg: dict[str, Any], root: Path) -> str:
    if cfg.get("num_cameras") or any((root / name).exists() for name in ("calibration_images", "camera_matrix", "corners", "undistortion")):
        return "3d"
    if cfg.get("multianimalproject") or cfg.get("bodyparts") == "MULTI!" or cfg.get("multianimalbodyparts"):
        return "multi-animal"
    return "standard"


def derive_bodyparts(cfg: dict[str, Any]) -> Any:
    if cfg.get("multianimalproject"):
        parts = cfg.get("multianimalbodyparts")
        return jsonable(parts if parts is not None else [])
    bodyparts = cfg.get("bodyparts")
    if bodyparts in (None, ""):
        return []
    if bodyparts == "MULTI!":
        return "MULTI!"
    return jsonable(bodyparts)


def sample_video_sets(video_sets: Any, limit: int) -> dict[str, Any]:
    if not isinstance(video_sets, dict):
        return {"count": 0, "sample": [], "kind": type(video_sets).__name__}

    entries: list[dict[str, Any]] = []
    for index, (video_path, info) in enumerate(sorted(video_sets.items(), key=lambda item: str(item[0]))):
        if index >= limit:
            break
        crop = None
        if isinstance(info, dict):
            crop = info.get("crop")
        entries.append(
            {
                "path": str(video_path),
                "exists": Path(str(video_path)).exists(),
                "crop": crop,
            }
        )

    return {
        "count": len(video_sets),
        "sample": entries,
        "truncated": len(video_sets) > limit,
    }


def summarize_config(cfg: dict[str, Any], root: Path, config_path: Path, limit: int, input_kind: str) -> dict[str, Any]:
    stored_project_path = safe_str_path(cfg.get("project_path"))
    resolved_project_path = Path(stored_project_path).expanduser() if stored_project_path else None
    project_path_matches_root = (
        resolved_project_path is not None and resolved_project_path.resolve() == root.resolve()
    )

    project_type = detect_project_type(cfg, root)
    project_summary: dict[str, Any] = {
        "Task": cfg.get("Task"),
        "scorer": cfg.get("scorer"),
        "date": cfg.get("date"),
        "project_path": stored_project_path,
        "project_path_matches_root": project_path_matches_root,
        "project_type": project_type,
        "engine": cfg.get("engine"),
        "multianimalproject": bool(cfg.get("multianimalproject", False)),
        "identity": cfg.get("identity"),
        "TrainingFraction": jsonable(cfg.get("TrainingFraction")),
        "bodyparts": jsonable(cfg.get("bodyparts")),
        "bodyparts_list": derive_bodyparts(cfg),
        "multianimalbodyparts": jsonable(cfg.get("multianimalbodyparts")),
        "individuals": jsonable(cfg.get("individuals")),
        "uniquebodyparts": jsonable(cfg.get("uniquebodyparts")),
        "video_sets": sample_video_sets(cfg.get("video_sets", {}), limit),
    }

    if project_type == "3d":
        project_summary["three_d"] = {
            "num_cameras": cfg.get("num_cameras"),
            "camera_names": jsonable(cfg.get("camera_names")),
            "scorername_3d": cfg.get("scorername_3d"),
            "config_file_keys": sorted(key for key in cfg if key.startswith("config_file_camera-")),
            "shuffle_keys": sorted(key for key in cfg if key.startswith("shuffle_camera-")),
            "trainingsetindex_keys": sorted(key for key in cfg if key.startswith("trainingsetindex_camera-")),
        }

    directories = {name: list_directory(root / name, limit) for name in KNOWN_LAYOUT_DIRS}
    missing_expected = [name for name, entry in directories.items() if name in {"videos", "labeled-data", "training-datasets"} and not entry["exists"]]

    return {
        "ok": True,
        "input": {
            "config_path": str(config_path),
            "project_root": str(root),
            "kind": input_kind,
        },
        "project": project_summary,
        "directories": directories,
        "warnings": ([] if project_path_matches_root or stored_project_path is None else [
            f"project_path points to {stored_project_path!r} but the inspected root is {str(root)!r}",
        ]),
        "missing_expected_directories": missing_expected,
    }


def summarize_path(path: Path, limit: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": False,
        "input": {
            "path": str(path),
        },
        "project": {},
        "directories": {name: list_directory(path / name, limit) for name in KNOWN_LAYOUT_DIRS} if path.exists() and path.is_dir() else {},
        "warnings": [],
        "errors": [],
        "missing_expected_directories": [],
    }

    if not path.exists():
        result["errors"].append(f"path does not exist: {path}")
        return result

    if path.is_file():
        config_path = path
        root = path.parent
    else:
        config_path = path / "config.yaml"
        root = path

    result["input"]["config_path"] = str(config_path)
    result["input"]["project_root"] = str(root)
    result["input"]["kind"] = "config-file" if path.is_file() else "project-directory"

    if not config_path.exists():
        result["errors"].append(f"config file not found: {config_path}")
        result["ok"] = False
        result["directories"] = {name: list_directory(root / name, limit) for name in KNOWN_LAYOUT_DIRS}
        result["missing_expected_directories"] = [
            name for name in ("videos", "labeled-data", "training-datasets") if not (root / name).exists()
        ]
        return result

    try:
        from deeplabcut.core.config import read_config_as_dict
    except Exception as exc:  # pragma: no cover - import failure is environment-specific
        result["errors"].append(f"deeplabcut import failed: {type(exc).__name__}: {exc}")
        result["directories"] = {name: list_directory(root / name, limit) for name in KNOWN_LAYOUT_DIRS}
        return result

    try:
        cfg = read_config_as_dict(config_path)
    except Exception as exc:
        result["errors"].append(f"failed to read config: {type(exc).__name__}: {exc}")
        result["directories"] = {name: list_directory(root / name, limit) for name in KNOWN_LAYOUT_DIRS}
        return result

    result.update(summarize_config(cfg, root=root, config_path=config_path, limit=limit, input_kind="config-file" if path.is_file() else "project-directory"))
    result["ok"] = True
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize a DeepLabCut project directory or config.yaml.")
    parser.add_argument("path", help="Project root directory or config.yaml path")
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation level (default: 2)")
    parser.add_argument("--max-entries", type=int, default=10, help="Max sample entries to include per folder")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    path = Path(args.path).expanduser()
    limit = max(0, int(args.max_entries))

    if path.is_file() or path.is_dir():
        summary = summarize_path(path, limit=limit)
    else:
        summary = {
            "ok": False,
            "input": {"path": str(path)},
            "project": {},
            "directories": {},
            "warnings": [],
            "errors": [f"path does not exist: {path}"],
            "missing_expected_directories": [],
        }

    json.dump(summary, sys.stdout, indent=args.indent, sort_keys=False)
    sys.stdout.write("\n")
    return 0 if summary.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
