#!/usr/bin/env python3
"""Inspect a pix2pixHD training setup without launching training."""

from __future__ import annotations

import argparse
import fractions
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_train_command import RECIPE_SPECS, build_command, list_recipes, validate_repo_root  # noqa: E402


def probe_environment() -> dict:
    report: dict[str, object] = {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "fractions_gcd": hasattr(fractions, "gcd"),
    }
    warnings: list[str] = []

    try:
        import torch

        report["torch"] = torch.__version__
        report["torch_cuda_compiled"] = getattr(torch.version, "cuda", None)
        report["cuda_available"] = bool(torch.cuda.is_available())
        if report["cuda_available"]:
            report["cuda_device_count"] = torch.cuda.device_count()
            report["cuda_device_name"] = torch.cuda.get_device_name(0)
            props = torch.cuda.get_device_properties(0)
            total_gb = round(props.total_memory / (1024**3), 1)
            report["cuda_total_memory_gb"] = total_gb
        else:
            report["cuda_device_count"] = 0
    except Exception as exc:  # pragma: no cover - environment dependent
        report["torch_error"] = f"{type(exc).__name__}: {exc}"
        warnings.append("torch import failed; the training code cannot run in this environment.")

    try:
        import torchvision

        report["torchvision"] = torchvision.__version__
        report["torchvision_scale"] = hasattr(torchvision.transforms, "Scale")
    except Exception as exc:  # pragma: no cover - environment dependent
        report["torchvision_error"] = f"{type(exc).__name__}: {exc}"
        warnings.append("torchvision import failed; preprocessing and VGG helpers may not work.")

    try:
        import apex  # noqa: F401

        report["apex"] = "available"
    except Exception as exc:  # pragma: no cover - environment dependent
        report["apex"] = f"missing: {type(exc).__name__}"

    if not report.get("fractions_gcd", False):
        warnings.append("train.py still calls fractions.gcd() in lcm(); Python 3.13+ needs a compatibility patch or older interpreter.")

    if report.get("torchvision_scale") is False:
        warnings.append("legacy resize_and_crop is unsafe on torchvision 0.28.0 because transforms.Scale is absent.")

    if report.get("cuda_available") is False:
        warnings.append("training recipes are CUDA-first; CPU is not a supported execution target.")

    report["warnings"] = warnings
    return report


def collect_repo_paths(repo_root: Path) -> dict:
    paths = {
        "train_py": (repo_root / "train.py").exists(),
        "models_dir": (repo_root / "models").exists(),
        "options_dir": (repo_root / "options").exists(),
        "scripts_dir": (repo_root / "scripts").exists(),
        "data_dir": (repo_root / "data").exists(),
        "util_dir": (repo_root / "util").exists(),
        "encode_features_py": (repo_root / "encode_features.py").exists(),
        "precompute_feature_maps_py": (repo_root / "precompute_feature_maps.py").exists(),
    }
    return paths


def recipe_warnings(spec_key: str, env: dict, repo_paths: dict) -> list[str]:
    warnings: list[str] = []
    spec = RECIPE_SPECS[spec_key]
    if spec.needs_feature_helpers and not (repo_paths.get("encode_features_py") and repo_paths.get("precompute_feature_maps_py")):
        warnings.append("feature-helper scripts are missing; the feature-conditioned recipe cannot be completed from this repo root.")
    if spec.needs_apex and env.get("apex", "").startswith("missing"):
        warnings.append("this recipe requires NVIDIA Apex for `--fp16`.")
    if env.get("cuda_available") and spec.expected_gpu_count > 1:
        if int(env.get("cuda_device_count", 0)) < spec.expected_gpu_count:
            warnings.append(f"this recipe expects about {spec.expected_gpu_count} visible GPUs, but the environment reports fewer.")
    if env.get("cuda_available") and spec.expected_vram_gb is not None and "cuda_total_memory_gb" in env:
        if float(env["cuda_total_memory_gb"]) < float(spec.expected_vram_gb):
            warnings.append(f"the visible GPU memory is below the recipe's rough VRAM floor ({spec.expected_vram_gb} GiB).")
    return warnings


def build_recipe_report(repo_root: Path, spec_key: str, env: dict) -> dict:
    spec = RECIPE_SPECS[spec_key]
    repo_paths = collect_repo_paths(repo_root)
    command, _ = build_command(repo_root, spec_key)
    missing = validate_repo_root(repo_root, spec)
    return {
        "recipe": spec.key,
        "summary": spec.summary,
        "source_script": spec.source_script,
        "command": command,
        "notes": list(spec.notes),
        "repo_missing": missing,
        "warnings": recipe_warnings(spec_key, env, repo_paths),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect a pix2pixHD training setup without launching training.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", default=".", help="Path to the pix2pixHD repository root.")
    parser.add_argument("--recipe", choices=sorted(RECIPE_SPECS), help="Inspect one canonical recipe instead of all recipes.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human-readable report.")
    parser.add_argument("--list-recipes", action="store_true", help="List available recipes and exit.")
    return parser.parse_args()


def render_text_report(repo_root: Path, env: dict, recipes: list[dict]) -> str:
    lines: list[str] = []
    lines.append("pix2pixHD training setup")
    lines.append(f"repo root: {repo_root}")
    lines.append("")
    lines.append("paths:")
    repo_paths = collect_repo_paths(repo_root)
    for key in ["train_py", "models_dir", "options_dir", "scripts_dir", "data_dir", "util_dir", "encode_features_py", "precompute_feature_maps_py"]:
        lines.append(f"  {key}: {'yes' if repo_paths[key] else 'no'}")
    lines.append("")
    lines.append("environment:")
    for key in ["python", "executable", "torch", "torch_cuda_compiled", "cuda_available", "cuda_device_count", "cuda_device_name", "cuda_total_memory_gb", "torchvision", "torchvision_scale", "apex", "fractions_gcd"]:
        if key in env:
            lines.append(f"  {key}: {env[key]}")
    if env.get("warnings"):
        lines.append("")
        lines.append("environment warnings:")
        for warning in env["warnings"]:
            lines.append(f"  - {warning}")
    for recipe in recipes:
        lines.append("")
        lines.append(f"recipe {recipe['recipe']}:")
        lines.append(f"  source: {recipe['source_script']}")
        lines.append(f"  command: {recipe['command']}")
        if recipe["notes"]:
            lines.append("  notes:")
            for note in recipe["notes"]:
                lines.append(f"    - {note}")
        if recipe["warnings"]:
            lines.append("  warnings:")
            for warning in recipe["warnings"]:
                lines.append(f"    - {warning}")
        if recipe["repo_missing"]:
            lines.append("  missing_files:")
            for item in recipe["repo_missing"]:
                lines.append(f"    - {item}")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()

    if args.list_recipes:
        for spec in list_recipes():
            print(f"{spec.key}: {spec.summary} ({spec.source_script})")
        return 0

    if not repo_root.exists():
        print(f"Repository root does not exist: {repo_root}", file=sys.stderr)
        return 2

    repo_paths = collect_repo_paths(repo_root)
    missing_required = validate_repo_root(repo_root, RECIPE_SPECS[args.recipe or "512p"])
    core_missing = [name for name, ok in repo_paths.items() if name in {"train_py", "models_dir", "options_dir", "scripts_dir"} and not ok]
    if core_missing:
        print("Missing expected training files:", file=sys.stderr)
        for item in core_missing:
            print(f"- {item}", file=sys.stderr)
        return 2

    env = probe_environment()
    recipes_to_report = [args.recipe] if args.recipe else [spec.key for spec in list_recipes()]
    recipe_reports = [build_recipe_report(repo_root, spec_key, env) for spec_key in recipes_to_report]

    # If the selected recipe needs helper scripts and they are missing, treat this as a path validation failure.
    if args.recipe and missing_required:
        print("Missing expected files for the selected recipe:", file=sys.stderr)
        for item in missing_required:
            print(f"- {repo_root / item}", file=sys.stderr)
        return 2

    report = {
        "repo_root": str(repo_root),
        "environment": env,
        "paths": repo_paths,
        "recipes": recipe_reports,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(repo_root, env, recipe_reports))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
