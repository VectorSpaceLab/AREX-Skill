#!/usr/bin/env python3
"""Preflight pix2pixHD inference checkpoints and closely related feature paths.

This script checks the generator checkpoint first and then verifies the small
set of feature/data folders that would otherwise cause an inference run to fail.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

RECIPES = {
    "512p": {"name": "label2city_512p", "feature_recipe": False},
    "1024p": {"name": "label2city_1024p", "feature_recipe": False},
    "512p-feat": {"name": "label2city_512p_feat", "feature_recipe": True},
    "1024p-feat": {"name": "label2city_1024p_feat", "feature_recipe": True},
}


def resolve_repo_root(raw: str) -> Path:
    root = Path(raw).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"repo root does not exist: {root}")
    if not (root / "test.py").is_file():
        raise SystemExit(f"repo root does not look like pix2pixHD (missing test.py): {root}")
    return root


def resolve_default_path(repo_root: Path, raw: str | None, relative_default: str) -> Path:
    path = Path(raw or relative_default).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def label_suffix(label_nc: int) -> str:
    return "_A" if label_nc == 0 else "_label"


def image_suffix(label_nc: int) -> str:
    return "_B" if label_nc == 0 else "_img"


def build_report(args: argparse.Namespace, repo_root: Path) -> dict:
    recipe = RECIPES[args.recipe]
    name = args.name or recipe["name"]
    checkpoints_dir = resolve_default_path(repo_root, args.checkpoints_dir, "checkpoints")
    dataroot = resolve_default_path(repo_root, args.dataroot, "datasets/cityscapes")
    exp_dir = checkpoints_dir / name
    generator_path = exp_dir / f"{args.which_epoch}_net_G.pth"
    encoder_path = exp_dir / f"{args.which_epoch}_net_E.pth"
    cluster_name = args.cluster_path or "features_clustered_010.npy"
    if Path(cluster_name).expanduser().is_absolute():
        raise SystemExit("cluster-path must be relative to checkpoints/<name>/, not an absolute path")
    cluster_path = exp_dir / cluster_name

    feature_mode = recipe["feature_recipe"] or args.instance_feat or args.label_feat
    warnings: list[str] = []
    if args.use_encoded_image and not feature_mode:
        warnings.append("use_encoded_image is set without feature mode; add --instance-feat or --label-feat so the flag has an effect.")
    if args.load_features:
        warnings.append("load_features belongs to the feature workflow; it expects precomputed phase_feat folders, not the sampled cluster cache.")

    required: list[Path] = [generator_path]
    optional: list[Path] = [encoder_path]

    label_dir = dataroot / f"{args.phase}{label_suffix(args.label_nc)}"
    inst_dir = dataroot / f"{args.phase}_inst"
    image_dir = dataroot / f"{args.phase}{image_suffix(args.label_nc)}"
    feat_dir = dataroot / f"{args.phase}_feat"

    if not args.use_encoded_image:
        optional.append(image_dir)
    if not args.load_features:
        optional.append(feat_dir)

    required.extend([label_dir, inst_dir])
    if args.use_encoded_image:
        required.append(image_dir)
    if args.load_features:
        required.append(feat_dir)
    if feature_mode and not args.use_encoded_image:
        required.append(cluster_path)
    elif feature_mode and args.use_encoded_image:
        optional.append(cluster_path)

    missing_required = [path for path in required if not path.exists()]
    missing_optional = [path for path in optional if not path.exists()]

    available_generators = sorted(p.name for p in exp_dir.glob("*_net_G.pth")) if exp_dir.exists() else []
    available_clusters = sorted(p.name for p in exp_dir.glob("*.npy")) if exp_dir.exists() else []

    if not generator_path.exists():
        if available_generators:
            warnings.append("Generator checkpoint missing for the requested epoch, but other generator checkpoints exist in the experiment directory.")
        else:
            warnings.append("No generator checkpoints were found in the experiment directory.")

    if args.use_encoded_image and not encoder_path.exists():
        warnings.append("The encoder checkpoint is absent; the encoded-image path may still run, but it will not use a trained netE.")

    if feature_mode and not args.use_encoded_image and not cluster_path.exists():
        if available_clusters:
            warnings.append("The expected cluster file is missing, but other .npy files exist in the experiment directory.")
        else:
            warnings.append("No feature-cluster cache was found in the experiment directory.")

    return {
        "repo_root": str(repo_root),
        "recipe": args.recipe,
        "name": name,
        "phase": args.phase,
        "which_epoch": args.which_epoch,
        "checkpoints_dir": str(checkpoints_dir),
        "dataroot": str(dataroot),
        "feature_mode": feature_mode,
        "use_encoded_image": args.use_encoded_image,
        "load_features": args.load_features,
        "paths": {
            "generator": str(generator_path),
            "encoder": str(encoder_path),
            "cluster": str(cluster_path),
            "label_dir": str(label_dir),
            "inst_dir": str(inst_dir),
            "image_dir": str(image_dir),
            "feat_dir": str(feat_dir),
        },
        "missing_required": [str(path) for path in missing_required],
        "missing_optional": [str(path) for path in missing_optional],
        "available_generators": available_generators,
        "available_clusters": available_clusters,
        "warnings": warnings,
    }


def render_text(report: dict) -> str:
    lines: list[str] = []
    for warning in report["warnings"]:
        lines.append(f"WARNING: {warning}")
    if report["missing_required"]:
        lines.append("MISSING REQUIRED PATHS:")
        for path in report["missing_required"]:
            lines.append(f"- {path}")
        if report["available_generators"]:
            lines.append("Available generator checkpoints:")
            for name in report["available_generators"]:
                lines.append(f"- {name}")
        if report["available_clusters"]:
            lines.append("Available feature caches:")
            for name in report["available_clusters"]:
                lines.append(f"- {name}")
        lines.append("Next step: fix the name/epoch/path selection or generate the missing checkpoint or feature cache.")
    else:
        lines.append(f"OK: generator checkpoint found at {report['paths']['generator']}")
        lines.append(f"OK: label directory found at {report['paths']['label_dir']}")
        lines.append(f"OK: instance directory found at {report['paths']['inst_dir']}")
        if Path(report["paths"]["encoder"]).exists() and (report["use_encoded_image"] or report["feature_mode"]):
            prefix = "OK" if report["use_encoded_image"] else "INFO"
            lines.append(f"{prefix}: encoder checkpoint found at {report['paths']['encoder']}")
        if report["paths"]["image_dir"] in report["missing_optional"]:
            lines.append(f"INFO: image directory not required for this command: {report['paths']['image_dir']}")
        elif Path(report["paths"]["image_dir"]).exists():
            lines.append(f"OK: image directory found at {report['paths']['image_dir']}")
        if report["paths"]["feat_dir"] in report["missing_optional"]:
            lines.append(f"INFO: feature directory not required for this command: {report['paths']['feat_dir']}")
        elif Path(report["paths"]["feat_dir"]).exists():
            lines.append(f"OK: feature directory found at {report['paths']['feat_dir']}")
        if report["feature_mode"] and Path(report["paths"]["cluster"]).exists() and report["paths"]["cluster"] not in report["missing_required"]:
            lines.append(f"OK: cluster cache found at {report['paths']['cluster']}")
        elif report["feature_mode"] and report["paths"]["cluster"] not in report["missing_required"]:
            lines.append(f"INFO: encoder/cluster files are optional for the encoded-image path: {report['paths']['cluster']}")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preflight pix2pixHD inference checkpoints and feature paths.")
    parser.add_argument("--repo-root", required=True, help="Path to the pix2pixHD checkout.")
    parser.add_argument("--recipe", choices=sorted(RECIPES), default="1024p", help="Inference recipe to validate.")
    parser.add_argument("--name", help="Override the experiment name; defaults to the selected recipe name.")
    parser.add_argument("--which-epoch", default="latest", help="Checkpoint suffix to check.")
    parser.add_argument("--phase", default="test", help="Dataset phase to check for inference data folders.")
    parser.add_argument("--checkpoints-dir", help="Override the checkpoint root; relative paths are resolved from --repo-root.")
    parser.add_argument("--dataroot", help="Override the dataset root; relative paths are resolved from --repo-root.")
    parser.add_argument("--label-nc", type=int, default=35, help="Number of label channels used by the recipe.")
    parser.add_argument("--cluster-path", help="Feature-cluster filename stored under checkpoints/<name>/.")
    parser.add_argument("--instance-feat", action="store_true", help="Expect feature conditioning via instance maps.")
    parser.add_argument("--label-feat", action="store_true", help="Expect feature conditioning via label maps.")
    parser.add_argument("--use-encoded-image", action="store_true", help="Check the paired-image folder needed by the encoded-image path.")
    parser.add_argument("--load-features", action="store_true", help="Check the phase_feat folder used by precomputed feature maps.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human-readable report.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = resolve_repo_root(args.repo_root)
    report = build_report(args, repo_root)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report), end="")
    return 1 if report["missing_required"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
