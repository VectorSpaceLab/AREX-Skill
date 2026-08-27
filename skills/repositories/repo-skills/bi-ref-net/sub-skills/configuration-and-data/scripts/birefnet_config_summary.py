#!/usr/bin/env python3
"""Print a BiRefNet configuration summary without importing source code."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DEFAULTS = {
    "task": "DIS5K",
    "testsets": "DIS-VD",
    "training_set": "DIS-TR",
    "size": [1024, 1024],
    "dynamic_size": None,
    "background_color_synthesis": False,
    "load_all": False,
    "auxiliary_classification": False,
    "mixed_precision": "bf16",
    "compile": True,
    "SDPA_enabled": True,
    "bb": "swin_v1_l",
    "model": "BiRefNet",
    "device": 0,
    "optimizer": "AdamW",
    "batch_size": 8,
    "batch_size_valid": 1,
    "num_workers": 8,
    "rand_seed": 7,
    "data_root_dir": "<sys_home_dir>/datasets/dis",
    "weights_root_dir": "<sys_home_dir>/weights/cv",
    "lambdas_pix_last": {
        "bce": 30,
        "iou": 0.5,
        "iou_patch": 0.0,
        "mae": 0,
        "mse": 0,
        "triplet": 0,
        "reg": 0,
        "ssim": 10,
        "cnt": 0,
        "structure": 0,
    },
    "lambdas_cls": {"ce": 5.0},
}

TASK_PROFILES = {
    "DIS5K": {
        "testsets": ["DIS-VD"],
        "training_set": "DIS-TR",
        "size": [1024, 1024],
        "loss_family": "segmentation",
    },
    "COD": {
        "testsets": ["CHAMELEON", "NC4K", "TE-CAMO", "TE-COD10K"],
        "training_set": "TR-COD10K+TR-CAMO",
        "size": [1024, 1024],
        "loss_family": "segmentation",
    },
    "HRSOD": {
        "testsets": ["DAVIS-S", "TE-HRSOD", "TE-UHRSD", "DUT-OMRON", "TE-DUTS"],
        "training_set": "TR-DUTS+TR-HRSOD+TR-UHRSD",
        "size": [1024, 1024],
        "loss_family": "segmentation",
    },
    "General": {
        "testsets": ["DIS-VD", "TE-P3M-500-NP"],
        "training_set": "auto-discovered",
        "size": [1024, 1024],
        "loss_family": "segmentation+mae",
    },
    "General-2K": {
        "testsets": ["DIS-VD", "TE-P3M-500-NP"],
        "training_set": "auto-discovered",
        "size": [2560, 1440],
        "loss_family": "segmentation+mae",
    },
    "Matting": {
        "testsets": ["TE-P3M-500-NP", "TE-AM-2k"],
        "training_set": "auto-discovered",
        "size": [1024, 1024],
        "loss_family": "matting",
    },
}

TASK_SCHEDULE = {
    "DIS5K": {"epochs": 500, "val_last": 50, "step": 5},
    "COD": {"epochs": 150, "val_last": 50, "step": 5},
    "HRSOD": {"epochs": 150, "val_last": 50, "step": 5},
    "General": {"epochs": 200, "val_last": 50, "step": 5},
    "General-2K": {"epochs": 250, "val_last": 30, "step": 2},
    "Matting": {"epochs": 150, "val_last": 50, "step": 5},
}

BACKBONES = [
    "vgg16",
    "vgg16bn",
    "resnet50",
    "swin_v1_l",
    "swin_v1_b",
    "swin_v1_s",
    "swin_v1_t",
    "pvt_v2_b5",
    "pvt_v2_b2",
    "pvt_v2_b1",
    "pvt_v2_b0",
    "dino_v3_7b",
    "dino_v3_h_plus",
    "dino_v3_l",
    "dino_v3_b",
    "dino_v3_s_plus",
    "dino_v3_s",
]

TRAIN_SH_RE = re.compile(
    r"['\"](?P<task>[^'\"]+)['\"]\)\s*epochs=(?P<epochs>\d+)\s*&&\s*val_last=(?P<val_last>\d+)\s*&&\s*step=(?P<step>\d+)"
)


def parse_train_sh(path: Path) -> dict[str, dict[str, int]]:
    schedule: dict[str, dict[str, int]] = {}
    if not path.is_file():
        return schedule
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = TRAIN_SH_RE.search(line)
        if match:
            schedule[match.group("task")] = {
                "epochs": int(match.group("epochs")),
                "val_last": int(match.group("val_last")),
                "step": int(match.group("step")),
            }
    return schedule


def build_summary(repo_root: Path | None) -> dict:
    summary = {
        "defaults": DEFAULTS,
        "task_profiles": TASK_PROFILES,
        "backbones": BACKBONES,
        "schedule": TASK_SCHEDULE,
        "repository_inspection": {
            "enabled": False,
            "train_sh_found": False,
            "schedule_source": "distilled defaults",
        },
    }
    if repo_root is None:
        return summary

    inspected = parse_train_sh(repo_root / "train.sh")
    if inspected:
        summary["schedule"] = inspected
        summary["repository_inspection"] = {
            "enabled": True,
            "train_sh_found": True,
            "schedule_source": "repository train.sh",
        }
    else:
        summary["repository_inspection"] = {
            "enabled": True,
            "train_sh_found": False,
            "schedule_source": "distilled defaults",
        }
    return summary


def fmt_value(value):
    if isinstance(value, list):
        return " x ".join(str(v) for v in value)
    if isinstance(value, dict):
        return ", ".join(f"{k}={v}" for k, v in value.items())
    return str(value)


def print_text(summary: dict) -> None:
    print("BiRefNet configuration summary")
    print()
    print("Defaults")
    for key in [
        "task",
        "testsets",
        "training_set",
        "size",
        "dynamic_size",
        "background_color_synthesis",
        "load_all",
        "auxiliary_classification",
        "mixed_precision",
        "compile",
        "SDPA_enabled",
        "bb",
        "model",
        "device",
        "optimizer",
        "batch_size",
        "batch_size_valid",
        "num_workers",
        "rand_seed",
        "data_root_dir",
        "weights_root_dir",
        "lambdas_pix_last",
        "lambdas_cls",
    ]:
        print(f"- {key}: {fmt_value(summary['defaults'][key])}")

    print()
    print("Task profiles")
    for task, profile in summary["task_profiles"].items():
        print(
            f"- {task}: testsets={', '.join(profile['testsets'])}; "
            f"training_set={profile['training_set']}; size={fmt_value(profile['size'])}; "
            f"loss_family={profile['loss_family']}"
        )

    print()
    print("Backbone choices")
    print("- " + ", ".join(summary["backbones"]))

    print()
    print("Save schedule")
    for task, schedule in summary["schedule"].items():
        print(
            f"- {task}: epochs={schedule['epochs']}, val_last={schedule['val_last']}, step={schedule['step']}"
        )

    print()
    inspection = summary["repository_inspection"]
    print(
        "Repository inspection: "
        f"enabled={inspection['enabled']}, train_sh_found={inspection['train_sh_found']}, "
        f"schedule_source={inspection['schedule_source']}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print a distilled BiRefNet config summary with optional repository schedule inspection."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Optional repository root to inspect for the local train.sh schedule.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the summary as JSON instead of text.",
    )
    args = parser.parse_args()

    summary = build_summary(args.repo_root)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_text(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
