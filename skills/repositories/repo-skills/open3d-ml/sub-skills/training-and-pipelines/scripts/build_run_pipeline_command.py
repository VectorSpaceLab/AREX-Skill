#!/usr/bin/env python3
"""Build an Open3D-ML pipeline-launch argument plan without running training.

The output is a command-shape aid and config inspector. It does not import
Open3D, open datasets, download checkpoints, launch the upstream source script,
or start training/evaluation.
"""
from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path


def load_yaml_names(config_path: str | None):
    if not config_path:
        return {}, []
    path = Path(config_path)
    warnings = []
    if not path.exists():
        return {}, [f"config file does not exist: {config_path}"]
    try:
        import yaml
    except Exception as exc:
        return {}, [f"PyYAML unavailable; cannot inspect config: {type(exc).__name__}: {exc}"]
    try:
        with path.open() as f:
            cfg = yaml.safe_load(f) or {}
    except Exception as exc:
        return {}, [f"failed to read YAML config: {type(exc).__name__}: {exc}"]
    names = {}
    for section in ("dataset", "model", "pipeline"):
        value = cfg.get(section, {}) if isinstance(cfg, dict) else {}
        names[section] = value.get("name") if isinstance(value, dict) else None
    return names, warnings


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build a safe Open3D-ML pipeline argument plan.")
    parser.add_argument("framework", choices=["torch", "tf"], help="Deep learning framework namespace.")
    parser.add_argument("-c", "--config", help="Combined YAML config with dataset/model/pipeline sections.")
    parser.add_argument("-p", "--pipeline", help="Pipeline name such as SemanticSegmentation or ObjectDetection.")
    parser.add_argument("-m", "--model", help="Model name such as RandLANet, KPFCNN, PointPillars.")
    parser.add_argument("-d", "--dataset", help="Dataset class name such as SemanticKITTI, KITTI, Custom3D.")
    parser.add_argument("--dataset-path", help="Dataset root path to pass as dataset_path.")
    parser.add_argument("--checkpoint", help="Checkpoint path to pass as ckpt_path.")
    parser.add_argument("--device", default="cpu", help="Device string. Use cpu for smoke checks; cuda/gpu requires a compatible backend.")
    parser.add_argument("--split", default="train", help="Split or mode, commonly train/test/validation.")
    parser.add_argument("--max-epochs", help="Optional max epoch override.")
    parser.add_argument("--batch-size", help="Optional batch size override.")
    parser.add_argument("--extra", action="append", default=[], metavar="KEY=VALUE", help="Extra dotted override, e.g. dataset.use_cache=True.")
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    args = parser.parse_args(argv)

    names, warnings = load_yaml_names(args.config)
    pipeline = args.pipeline or names.get("pipeline")
    model = args.model or names.get("model")
    dataset = args.dataset or names.get("dataset")

    errors = []
    if not args.config and not (pipeline and model and dataset):
        errors.append("provide either --config or all of --pipeline, --model, and --dataset")
    for item in args.extra:
        if "=" not in item:
            errors.append(f"extra override must be KEY=VALUE: {item}")

    launcher_args = [args.framework]
    if args.config:
        launcher_args += ["-c", args.config]
    else:
        launcher_args += ["-p", pipeline or "<PIPELINE>", "-m", model or "<MODEL>", "-d", dataset or "<DATASET>"]
    launcher_args += ["--split", args.split, "--device", args.device]
    if args.dataset_path:
        launcher_args += ["--dataset_path", args.dataset_path]
    if args.checkpoint:
        launcher_args += ["--ckpt_path", args.checkpoint]
    if args.max_epochs:
        launcher_args += ["--max_epochs", str(args.max_epochs)]
    if args.batch_size:
        launcher_args += ["--batch_size", str(args.batch_size)]
    for item in args.extra:
        key, value = item.split("=", 1)
        launcher_args += [f"--{key}", value]

    report = {
        "status": "ok" if not errors else "error",
        "framework": args.framework,
        "config_names": names,
        "selected": {"pipeline": pipeline, "model": model, "dataset": dataset},
        "upstream_compatible_args": launcher_args,
        "shell_fragment": " ".join(shlex.quote(x) for x in launcher_args),
        "does_not_run_training": True,
        "warnings": warnings,
        "errors": errors,
        "notes": [
            "Use these arguments with an Open3D-ML pipeline launcher only when you intentionally have one in your working project.",
            "For self-contained direct API usage, follow references/workflows.md instead of depending on a source checkout script.",
        ],
    }

    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
