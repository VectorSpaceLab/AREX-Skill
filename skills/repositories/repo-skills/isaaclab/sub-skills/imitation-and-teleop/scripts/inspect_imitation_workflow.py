#!/usr/bin/env python3
"""Summarize Isaac Lab imitation, teleoperation, and augmentation prerequisites."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from typing import Any

WORKFLOW_PROFILES = {
    "teleop": {
        "summary": "Interactive teleoperation for demo collection.",
        "requires": ["task id", "simulation backend", "teleop device or XR stack"],
        "optional_packages": ["isaaclab_teleop", "dex-retargeting"],
        "hardware": ["keyboard or SpaceMouse", "XR device if using CloudXR"],
    },
    "record": {
        "summary": "Record human demonstrations to an HDF5 dataset.",
        "requires": ["task id", "dataset path", "simulation backend"],
        "optional_packages": ["isaaclab_teleop", "robomimic"],
        "hardware": ["teleop input device"],
    },
    "annotate": {
        "summary": "Annotate demonstrations with Mimic subtask signals.",
        "requires": ["input HDF5 dataset", "output HDF5 dataset", "task id or env name"],
        "optional_packages": ["isaaclab_mimic"],
        "hardware": ["simulation backend for interactive annotation"],
    },
    "generate": {
        "summary": "Generate synthetic demonstrations from annotated data.",
        "requires": ["annotated HDF5 dataset", "output HDF5 dataset", "task id or env name"],
        "optional_packages": ["isaaclab_mimic", "robomimic"],
        "hardware": ["simulation backend", "GPU helpful for larger runs"],
    },
    "skillgen": {
        "summary": "Plan motion between annotated subtask segments.",
        "requires": ["annotated HDF5 dataset", "subtask start and termination signals"],
        "optional_packages": ["isaaclab_mimic", "curobo"],
        "hardware": ["GPU", "supported CUDA stack", "robust motion-planning environment"],
    },
    "convert-hdf5-mp4": {
        "summary": "Export camera observations to MP4 files.",
        "requires": ["input HDF5 dataset", "output directory"],
        "optional_packages": ["opencv-python", "h5py"],
        "hardware": ["codec support", "camera data in the dataset"],
    },
    "convert-mp4-hdf5": {
        "summary": "Replace visual observations with augmented MP4 frames.",
        "requires": ["input HDF5 dataset", "videos directory", "output HDF5 dataset"],
        "optional_packages": ["opencv-python", "h5py"],
        "hardware": ["codec support"],
    },
    "merge": {
        "summary": "Merge multiple HDF5 demonstration datasets.",
        "requires": ["two or more HDF5 datasets", "output HDF5 dataset"],
        "optional_packages": ["h5py"],
        "hardware": [],
    },
    "cosmos-prompts": {
        "summary": "Generate prompt text for Cosmos visual augmentation.",
        "requires": ["prompt-template JSON", "output text path"],
        "optional_packages": [],
        "hardware": [],
    },
}


@dataclass
class WorkflowReport:
    workflow: str
    summary: str
    requires: list[str] = field(default_factory=list)
    optional_packages: list[str] = field(default_factory=list)
    hardware: list[str] = field(default_factory=list)
    inputs: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow": self.workflow,
            "summary": self.summary,
            "requires": self.requires,
            "optional_packages": self.optional_packages,
            "hardware": self.hardware,
            "inputs": self.inputs,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Isaac Lab imitation and teleoperation workflows.")
    parser.add_argument(
        "workflow",
        choices=sorted(WORKFLOW_PROFILES),
        help="Which workflow family to summarize.",
    )
    parser.add_argument("--task", type=str, default=None)
    parser.add_argument("--dataset", type=str, default=None)
    parser.add_argument("--input", type=str, default=None)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--teleop_device", type=str, default=None)
    parser.add_argument("--device", type=str, default=None)
    parser.add_argument("--num_envs", type=int, default=None)
    parser.add_argument("--use_skillgen", action="store_true", default=False)
    parser.add_argument("--xr", action="store_true", default=False)
    parser.add_argument("--camera", action="store_true", default=False)
    args = parser.parse_args()

    profile = WORKFLOW_PROFILES[args.workflow]
    inputs = {key: value for key, value in vars(args).items() if key not in {"workflow"} and value not in {None, False}}
    if args.use_skillgen:
        inputs["use_skillgen"] = True
    if args.xr:
        inputs["xr"] = True
    if args.camera:
        inputs["camera"] = True

    report = WorkflowReport(
        workflow=args.workflow,
        summary=profile["summary"],
        requires=list(profile["requires"]),
        optional_packages=list(profile["optional_packages"]),
        hardware=list(profile["hardware"]),
        inputs=inputs,
    )
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
