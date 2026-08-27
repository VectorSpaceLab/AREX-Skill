#!/usr/bin/env python3
"""Build safe pix2pixHD inference commands from an explicit repo root.

The script prints commands only. It never executes `test.py` or `encode_features.py`.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path

RECIPES = {
    "512p": {
        "name": "label2city_512p",
        "test_flags": [],
        "prep_flags": [],
        "feature_recipe": False,
    },
    "1024p": {
        "name": "label2city_1024p",
        "test_flags": ["--netG", "local", "--ngf", "32", "--resize_or_crop", "none"],
        "prep_flags": ["--netG", "local", "--ngf", "32", "--resize_or_crop", "none"],
        "feature_recipe": False,
    },
    "512p-feat": {
        "name": "label2city_512p_feat",
        "test_flags": ["--instance_feat"],
        "prep_flags": [],
        "feature_recipe": True,
    },
    "1024p-feat": {
        "name": "label2city_1024p_feat",
        "test_flags": ["--netG", "local", "--ngf", "32", "--resize_or_crop", "none", "--instance_feat"],
        "prep_flags": ["--netG", "local", "--ngf", "32", "--resize_or_crop", "none"],
        "feature_recipe": True,
    },
}

MODES = {"standard", "export-onnx", "engine", "onnx"}


def quote_cmd(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


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


def append_flag(parts: list[str], flag: str, value: str | int | None = None) -> None:
    if value is None:
        parts.append(flag)
    else:
        parts.extend([flag, str(value)])


def build_common_flags(args: argparse.Namespace, repo_root: Path, name: str) -> list[str]:
    checkpoints_dir = resolve_default_path(repo_root, args.checkpoints_dir, "checkpoints")
    results_dir = resolve_default_path(repo_root, args.results_dir, "results")
    dataroot = resolve_default_path(repo_root, args.dataroot, "datasets/cityscapes")

    flags: list[str] = []
    append_flag(flags, "--name", name)
    append_flag(flags, "--which_epoch", args.which_epoch)
    append_flag(flags, "--phase", args.phase)
    append_flag(flags, "--gpu_ids", args.gpu_ids)
    append_flag(flags, "--how_many", args.how_many)
    append_flag(flags, "--dataroot", str(dataroot))
    append_flag(flags, "--checkpoints_dir", str(checkpoints_dir))
    append_flag(flags, "--results_dir", str(results_dir))
    append_flag(flags, "--label_nc", args.label_nc)
    return flags


def build_feature_flags(args: argparse.Namespace, recipe: dict, warnings: list[str]) -> list[str]:
    flags: list[str] = []
    feature_flags: list[str] = []
    recipe_already_has_instance = recipe["feature_recipe"]

    if args.instance_feat and not recipe_already_has_instance:
        feature_flags.append("--instance_feat")
    if args.label_feat:
        feature_flags.append("--label_feat")

    if not feature_flags and not recipe_already_has_instance and (args.use_encoded_image or args.load_features):
        feature_flags.append("--instance_feat")
        warnings.append("Adding --instance_feat because the requested path needs feature mode.")

    flags.extend(feature_flags)

    if args.use_encoded_image:
        append_flag(flags, "--use_encoded_image")
    if args.load_features:
        append_flag(flags, "--load_features")
    return flags


def build_test_command(args: argparse.Namespace, repo_root: Path, recipe: dict, warnings: list[str]) -> tuple[str, dict[str, str]]:
    test_script = repo_root / "test.py"
    name = args.name or recipe["name"]
    common_flags = build_common_flags(args, repo_root, name)
    feature_flags = build_feature_flags(args, recipe, warnings)
    test_flags = list(recipe["test_flags"])
    test_flags.extend(feature_flags)

    cluster_path = args.cluster_path or "features_clustered_010.npy"
    if Path(cluster_path).expanduser().is_absolute():
        raise SystemExit("cluster_path must be relative to checkpoints/<name>/, not an absolute path")
    if ("--instance_feat" in test_flags or "--label_feat" in test_flags) and not args.use_encoded_image and not args.load_features:
        append_flag(test_flags, "--cluster_path", cluster_path)
    elif args.cluster_path and args.use_encoded_image:
        warnings.append("cluster_path was supplied but will be ignored because use_encoded_image takes the feature map from the paired image.")
    elif args.load_features:
        warnings.append("load_features uses precomputed phase_feat folders, so the sampled cluster_path is intentionally omitted from the command.")

    if args.mode == "export-onnx":
        export_target = resolve_default_path(repo_root, args.artifact_path, "artifacts/pix2pixhd.onnx")
        if export_target.suffix.lower() != ".onnx":
            raise SystemExit("ONNX export targets must end with .onnx")
        append_flag(test_flags, "--export_onnx", str(export_target))
    elif args.mode == "engine":
        append_flag(test_flags, "--engine", str(resolve_default_path(repo_root, args.artifact_path, "artifacts/pix2pixhd.engine")))
    elif args.mode == "onnx":
        onnx_target = resolve_default_path(repo_root, args.artifact_path, "artifacts/pix2pixhd.onnx")
        if onnx_target.suffix.lower() != ".onnx":
            raise SystemExit("TensorRT ONNX targets must end with .onnx")
        append_flag(test_flags, "--onnx", str(onnx_target))

    command = quote_cmd(["python", str(test_script), *test_flags, *common_flags])
    outputs = {
        "checkpoint": str((resolve_default_path(repo_root, args.checkpoints_dir, "checkpoints") / name / f"{args.which_epoch}_net_G.pth").resolve()),
        "html": str((resolve_default_path(repo_root, args.results_dir, "results") / name / f"{args.phase}_{args.which_epoch}" / "index.html").resolve()),
    }
    if ("--instance_feat" in test_flags or "--label_feat" in test_flags) and not args.use_encoded_image and not args.load_features:
        outputs["cluster_path"] = str((resolve_default_path(repo_root, args.checkpoints_dir, "checkpoints") / name / cluster_path).resolve())
    return command, outputs


def build_prep_command(args: argparse.Namespace, repo_root: Path, recipe: dict) -> str | None:
    if not (recipe["feature_recipe"] and args.include_feature_prep):
        return None

    prep_script = repo_root / "encode_features.py"
    name = args.name or recipe["name"]
    prep_flags = list(recipe["prep_flags"])
    common_flags: list[str] = []
    append_flag(common_flags, "--name", name)
    append_flag(common_flags, "--which_epoch", args.which_epoch)
    append_flag(common_flags, "--phase", "train")
    append_flag(common_flags, "--gpu_ids", args.gpu_ids)
    append_flag(common_flags, "--dataroot", str(resolve_default_path(repo_root, args.dataroot, "datasets/cityscapes")))
    append_flag(common_flags, "--checkpoints_dir", str(resolve_default_path(repo_root, args.checkpoints_dir, "checkpoints")))
    append_flag(common_flags, "--label_nc", args.label_nc)

    if args.mode != "standard":
        # The prep step always targets the standard feature cache.
        pass

    return quote_cmd(["python", str(prep_script), *prep_flags, *common_flags])


def build_report(args: argparse.Namespace, repo_root: Path) -> dict:
    recipe = RECIPES[args.recipe]
    warnings: list[str] = []

    if args.mode not in MODES:
        raise SystemExit(f"unsupported mode: {args.mode}")

    if args.mode in {"engine", "onnx"} and (args.use_encoded_image or args.load_features):
        warnings.append("The legacy TensorRT helper only receives label and instance tensors, so use_encoded_image/load_features will not affect the runtime path.")

    if args.mode == "export-onnx" and (args.use_encoded_image or args.load_features):
        warnings.append("The ONNX export path is export-only; feature-guided image inputs are not part of the exported forward signature.")

    if args.load_features:
        warnings.append("load_features belongs to the separate feature-map workflow; it is not the same thing as the sampled cluster cache.")

    test_command, outputs = build_test_command(args, repo_root, recipe, warnings)
    prep_command = build_prep_command(args, repo_root, recipe)

    return {
        "repo_root": str(repo_root),
        "recipe": args.recipe,
        "mode": args.mode,
        "commands": [cmd for cmd in [prep_command, test_command] if cmd],
        "outputs": outputs,
        "warnings": warnings,
    }


def render_text(report: dict) -> str:
    lines: list[str] = []
    for warning in report["warnings"]:
        lines.append(f"# WARNING: {warning}")
    lines.append(f"# repo_root: {report['repo_root']}")
    lines.append(f"# recipe: {report['recipe']}")
    lines.append(f"# mode: {report['mode']}")
    if report["mode"] == "standard":
        lines.append(f"# expected HTML: {report['outputs']['html']}")
    elif report["mode"] == "export-onnx":
        lines.append("# export-only path; no HTML synthesis is produced by this command")
    else:
        lines.append("# reference-only accelerator path; HTML parity is not guaranteed by the checked-in helper")
    lines.append(f"# expected generator checkpoint: {report['outputs']['checkpoint']}")
    if "cluster_path" in report["outputs"]:
        lines.append(f"# expected cluster cache: {report['outputs']['cluster_path']}")
    lines.append("")
    lines.extend(report["commands"])
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build safe pix2pixHD inference commands from an explicit repo root.")
    parser.add_argument("--repo-root", required=True, help="Path to the pix2pixHD checkout.")
    parser.add_argument("--recipe", choices=sorted(RECIPES), required=True, help="Inference recipe to build.")
    parser.add_argument("--mode", choices=sorted(MODES), default="standard", help="Standard synthesis, ONNX export, or a reference-only accelerator path.")
    parser.add_argument("--artifact-path", help="Output file for export-onnx, engine, or onnx modes.")
    parser.add_argument("--name", help="Override the experiment name; defaults to the selected recipe name.")
    parser.add_argument("--which-epoch", default="latest", help="Checkpoint suffix to load.")
    parser.add_argument("--phase", default="test", help="Inference phase used in the results path.")
    parser.add_argument("--gpu-ids", default="0", help="GPU id string passed to test.py.")
    parser.add_argument("--how-many", type=int, default=50, help="Maximum number of samples to process.")
    parser.add_argument("--dataroot", help="Override the dataset root; relative paths are resolved from --repo-root.")
    parser.add_argument("--checkpoints-dir", help="Override the checkpoint root; relative paths are resolved from --repo-root.")
    parser.add_argument("--results-dir", help="Override the results root; relative paths are resolved from --repo-root.")
    parser.add_argument("--label-nc", type=int, default=35, help="Number of label channels used by the recipe.")
    parser.add_argument("--cluster-path", help="Feature-cluster filename stored under checkpoints/<name>/.")
    parser.add_argument("--instance-feat", action="store_true", help="Append --instance_feat to the generated command.")
    parser.add_argument("--label-feat", action="store_true", help="Append --label_feat to the generated command.")
    parser.add_argument("--use-encoded-image", action="store_true", help="Append --use_encoded_image to the generated command.")
    parser.add_argument("--load-features", action="store_true", help="Append --load_features to the generated command.")
    parser.add_argument("--include-feature-prep", action="store_true", help="Also print the matching encode_features.py command for feature recipes.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of shell text.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = resolve_repo_root(args.repo_root)
    report = build_report(args, repo_root)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
