#!/usr/bin/env python3
"""Inspect a ManiSkill .h5/.json trajectory bundle without modifying it."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import h5py  # type: ignore
except Exception as exc:  # pragma: no cover - depends on user env
    h5py = None
    H5PY_ERROR = exc
else:
    H5PY_ERROR = None


def load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:
        return None, str(exc)


def summarize_h5(path: Path) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    summary: dict[str, Any] = {
        "traj_count": None,
        "traj_keys": [],
        "first_traj_key": None,
        "first_traj_fields": [],
        "has_actions": None,
        "has_env_states": None,
        "has_obs": None,
        "has_rewards": None,
        "has_success": None,
        "has_fail": None,
    }
    if h5py is None:
        warnings.append(f"h5py import failed: {H5PY_ERROR}")
        return summary, warnings
    try:
        with h5py.File(path, "r") as f:
            traj_keys = sorted(k for k in f.keys() if k.startswith("traj_"))
            summary["traj_keys"] = traj_keys[:20]
            summary["traj_count"] = len(traj_keys)
            if traj_keys:
                first = f[traj_keys[0]]
                fields = sorted(first.keys())
                summary["first_traj_key"] = traj_keys[0]
                summary["first_traj_fields"] = fields
                summary["has_actions"] = "actions" in first
                summary["has_env_states"] = "env_states" in first
                summary["has_obs"] = "obs" in first
                summary["has_rewards"] = "rewards" in first
                summary["has_success"] = "success" in first
                summary["has_fail"] = "fail" in first
            else:
                warnings.append("no HDF5 keys starting with 'traj_' were found")
    except Exception as exc:
        warnings.append(f"could not inspect HDF5: {exc}")
    return summary, warnings


def build_report(traj_path: Path) -> dict[str, Any]:
    report: dict[str, Any] = {
        "ok": True,
        "h5_path": str(traj_path),
        "json_path": str(traj_path.with_suffix(".json")),
        "warnings": [],
        "metadata": {},
        "hdf5": {},
    }

    if traj_path.suffix != ".h5":
        report["warnings"].append("trajectory path should normally end in .h5")
    if not traj_path.exists():
        report["ok"] = False
        report["warnings"].append("HDF5 file does not exist")
        return report

    json_path = traj_path.with_suffix(".json")
    if not json_path.exists():
        report["ok"] = False
        report["warnings"].append("sibling JSON metadata file is missing")
    else:
        data, err = load_json(json_path)
        if err is not None or data is None:
            report["ok"] = False
            report["warnings"].append(f"could not load JSON metadata: {err}")
        else:
            env_info = data.get("env_info", {}) or {}
            env_kwargs = env_info.get("env_kwargs", {}) or {}
            episodes = data.get("episodes", []) or []
            control_modes = sorted({ep.get("control_mode") for ep in episodes if ep.get("control_mode")})
            report["metadata"] = {
                "env_id": env_info.get("env_id"),
                "max_episode_steps": env_info.get("max_episode_steps"),
                "sim_backend": env_kwargs.get("sim_backend"),
                "obs_mode": env_kwargs.get("obs_mode"),
                "control_modes": control_modes,
                "episode_count": len(episodes),
                "source_type": data.get("source_type"),
                "source_desc": data.get("source_desc"),
            }

    h5_summary, h5_warnings = summarize_h5(traj_path)
    report["hdf5"] = h5_summary
    report["warnings"].extend(h5_warnings)

    episode_count = report.get("metadata", {}).get("episode_count")
    traj_count = h5_summary.get("traj_count")
    if episode_count is not None and traj_count is not None and episode_count != traj_count:
        report["warnings"].append(
            f"JSON episode count ({episode_count}) does not match HDF5 traj_* count ({traj_count})"
        )
    return report


def print_text(report: dict[str, Any]) -> None:
    print(f"OK: {report['ok']}")
    print(f"HDF5: {report['h5_path']}")
    print(f"JSON: {report['json_path']}")
    metadata = report.get("metadata", {}) or {}
    if metadata:
        print("Metadata:")
        for key in ["env_id", "episode_count", "control_modes", "sim_backend", "obs_mode", "source_type", "source_desc"]:
            print(f"  {key}: {metadata.get(key)}")
    hdf5 = report.get("hdf5", {}) or {}
    if hdf5:
        print("HDF5 summary:")
        for key in ["traj_count", "first_traj_key", "first_traj_fields", "has_actions", "has_env_states", "has_obs", "has_rewards", "has_success", "has_fail"]:
            print(f"  {key}: {hdf5.get(key)}")
    if report.get("warnings"):
        print("Warnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traj_path", type=Path, help="Path to the ManiSkill trajectory .h5 file")
    parser.add_argument("--json", dest="as_json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when warnings are present, not only when required files are missing",
    )
    args = parser.parse_args(argv)

    report = build_report(args.traj_path)
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)

    if not report["ok"] or (args.strict and report.get("warnings")):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
