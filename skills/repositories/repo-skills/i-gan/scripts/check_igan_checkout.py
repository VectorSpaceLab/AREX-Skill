#!/usr/bin/env python3
"""Preflight an iGAN checkout without importing legacy runtime modules.

This script checks for the files, optional artifacts, GPU/display signals, and
common blockers that matter before running iGAN's original Theano/PyQt4 scripts.
It performs no downloads, no training, no GUI launch, and no GPU allocation.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
from typing import Dict, List, Optional

REQUIRED_FILES = [
    "README.md",
    "iGAN_main.py",
    "iGAN_script.py",
    "iGAN_predict.py",
    "generate_samples.py",
    "constrained_opt.py",
    "constrained_opt_theano.py",
    "model_def/dcgan_theano.py",
    "model_def/dcgan_theano_config.py",
    "train_dcgan/train_dcgan.py",
    "train_dcgan/create_hdf5.py",
]

MODEL_NAMES = ["outdoor_64", "church_64", "handbag_64", "shoes_64", "hed_shoes_64"]
DATASET_NAMES = [
    "outdoor_64",
    "outdoor_128",
    "church_64",
    "church_128",
    "shoes_64",
    "shoes_128",
    "handbag_64",
    "handbag_128",
    "sketch_shoes_64",
    "sketch_shoes_128",
    "hed_shoes_64",
    "hed_shoes_128",
]


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely inspect an iGAN checkout for expected files and runtime blockers.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", default=".", help="Path to an iGAN checkout to inspect.")
    parser.add_argument("--model-name", default="outdoor_64", choices=MODEL_NAMES, help="Model artifact to check.")
    parser.add_argument("--dataset-name", default=None, choices=DATASET_NAMES, help="Optional dataset artifact to check.")
    parser.add_argument("--alexnet-layer", default="conv4", help="Optional AlexNet layer artifact to check.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if required source files are missing.")
    return parser.parse_args(argv)


def nvidia_smi_summary() -> Dict[str, object]:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return {"available": False, "reason": "nvidia-smi not found"}
    try:
        out = subprocess.run(
            [exe, "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
    except Exception as exc:  # pragma: no cover - defensive host probe
        return {"available": False, "reason": str(exc)}
    if out.returncode != 0:
        return {"available": False, "reason": out.stderr.strip() or "nvidia-smi failed"}
    gpus = [line.strip() for line in out.stdout.splitlines() if line.strip()]
    return {"available": bool(gpus), "gpus": gpus}


def build_report(args: argparse.Namespace) -> Dict[str, object]:
    root = pathlib.Path(args.repo_root).expanduser().resolve()
    required = []
    for rel in REQUIRED_FILES:
        path = root / rel
        required.append({"path": rel, "exists": path.is_file()})

    model_path = root / "models" / f"{args.model_name}.dcgan_theano"
    alexnet_path = root / "models" / f"caffe_reference_{args.alexnet_layer}.pkl"
    dataset_path = root / "datasets" / f"{args.dataset_name}.hdf5" if args.dataset_name else None

    optional = [
        {"kind": "dcgan_model", "name": args.model_name, "path": str(model_path.relative_to(root)), "exists": model_path.is_file()},
        {"kind": "alexnet", "name": args.alexnet_layer, "path": str(alexnet_path.relative_to(root)), "exists": alexnet_path.is_file()},
    ]
    if dataset_path is not None:
        optional.append({"kind": "dataset", "name": args.dataset_name, "path": str(dataset_path.relative_to(root)), "exists": dataset_path.is_file()})

    blockers = []
    missing_required = [item["path"] for item in required if not item["exists"]]
    if missing_required:
        blockers.append("Missing expected iGAN source files: " + ", ".join(missing_required))
    if not model_path.is_file():
        blockers.append(f"Missing model artifact for {args.model_name}: models/{args.model_name}.dcgan_theano")
    if not os.environ.get("DISPLAY"):
        blockers.append("DISPLAY is unset; interactive PyQt4 UI launch needs a display or remote desktop session")
    gpu = nvidia_smi_summary()
    if not gpu.get("available"):
        blockers.append("No NVIDIA GPU signal from nvidia-smi; documented native generation/training expects CUDA")

    return {
        "repo_root": str(root),
        "required_files": required,
        "optional_artifacts": optional,
        "host_signals": {
            "display": os.environ.get("DISPLAY") or None,
            "python": sys.version.split()[0],
            "nvidia_smi": gpu,
        },
        "blockers": blockers,
        "side_effects": "none; no imports from the checkout, no downloads, no GPU allocation, no GUI launch",
    }


def emit_text(report: Dict[str, object]) -> None:
    print("iGAN checkout preflight")
    print(f"repo_root: {report['repo_root']}")
    missing = [item["path"] for item in report["required_files"] if not item["exists"]]
    print("required_files: {}".format("ok" if not missing else "missing " + ", ".join(missing)))
    for item in report["optional_artifacts"]:
        status = "present" if item["exists"] else "missing"
        print(f"artifact[{item['kind']}:{item['name']}]: {status} ({item['path']})")
    host = report["host_signals"]
    print(f"display: {host['display'] or 'unset'}")
    gpu = host["nvidia_smi"]
    if gpu.get("available"):
        print("nvidia_smi: available")
        for gpu_line in gpu.get("gpus", []):
            print(f"  gpu: {gpu_line}")
    else:
        print(f"nvidia_smi: unavailable ({gpu.get('reason')})")
    if report["blockers"]:
        print("blockers:")
        for blocker in report["blockers"]:
            print(f"  - {blocker}")
    else:
        print("blockers: none detected by static preflight")
    print(f"side_effects: {report['side_effects']}")


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    report = build_report(args)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        emit_text(report)
    if args.strict and any(not item["exists"] for item in report["required_files"]):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
