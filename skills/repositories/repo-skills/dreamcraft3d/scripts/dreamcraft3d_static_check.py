#!/usr/bin/env python3
"""Read-only DreamCraft3D checkout and skill helper checker.

This script checks repository-relative files, canonical configs, optional image
sidecars, and bundled helper presence. It does not import heavy ML packages,
download models, build Docker images, or launch training.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

CONFIGS = {
    "coarse_nerf": "configs/dreamcraft3d-coarse-nerf.yaml",
    "coarse_neus": "configs/dreamcraft3d-coarse-neus.yaml",
    "geometry": "configs/dreamcraft3d-geometry.yaml",
    "texture": "configs/dreamcraft3d-texture.yaml",
}
REQUIRED_ROOT_FILES = [
    "README.md",
    "requirements.txt",
    "launch.py",
    "preprocess_image.py",
    "gradio_app.py",
    "docs/installation.md",
    "threestudio/__init__.py",
    "threestudio/systems/dreamcraft3d.py",
    "threestudio/data/image.py",
]
REQUIRED_SKILL_FILES = [
    "SKILL.md",
    "references/repo-provenance.md",
    "references/repo-routing-metadata.json",
    "references/troubleshooting.md",
    "references/config-reference.md",
    "sub-skills/image-preparation/SKILL.md",
    "sub-skills/generation-pipeline/SKILL.md",
    "sub-skills/bootstrapped-texture/SKILL.md",
    "sub-skills/export-and-evaluation/SKILL.md",
    "sub-skills/interfaces-and-monitoring/SKILL.md",
]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def config_summary(path: Path) -> Dict[str, Any]:
    text = read_text(path)
    summary: Dict[str, Any] = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        return summary
    patterns = {
        "name": r"(?m)^name:\s*[\"']?([^\"'\n]+)",
        "data_type": r"(?m)^data_type:\s*[\"']?([^\"'\n]+)",
        "system_type": r"(?m)^system_type:\s*[\"']?([^\"'\n]+)",
        "stage": r"(?m)^\s+stage:\s*([^\n#]+)",
        "geometry_type": r"(?m)^\s+geometry_type:\s*[\"']?([^\"'\n]+)",
        "renderer_type": r"(?m)^\s+renderer_type:\s*[\"']?([^\"'\n]+)",
        "guidance_type": r"(?m)^\s+guidance_type:\s*[\"']?([^\"'\n]+)",
        "prompt_processor_type": r"(?m)^\s+prompt_processor_type:\s*[\"']?([^\"'\n]+)",
    }
    for key, pat in patterns.items():
        m = re.search(pat, text)
        if m:
            summary[key] = m.group(1).strip().strip('"\'')
    summary["has_mandatory_prompt"] = "prompt: ???" in text
    summary["has_geometry_convert_from"] = "geometry_convert_from: ???" in text
    return summary


def image_family(image: Path) -> Dict[str, Any]:
    if image.name.endswith("_rgba.png"):
        stem = image.name[: -len("_rgba.png")]
    else:
        stem = image.stem
    paths = {
        "rgba": image,
        "depth": image.with_name(f"{stem}_depth.png"),
        "normal": image.with_name(f"{stem}_normal.png"),
        "caption": image.with_name(f"{stem}_caption.txt"),
    }
    return {key: {"path": str(path), "exists": path.exists()} for key, path in paths.items()}


def check(args: argparse.Namespace) -> Dict[str, Any]:
    repo = Path(args.repo_root).resolve()
    skill = Path(args.skill_dir).resolve() if args.skill_dir else Path(__file__).resolve().parents[1]
    problems: List[str] = []
    warnings: List[str] = []

    repo_paths = {}
    for rel in REQUIRED_ROOT_FILES:
        p = repo / rel
        repo_paths[rel] = p.exists()
        if not p.exists():
            problems.append(f"missing repository evidence file: {rel}")
    for rel in CONFIGS.values():
        p = repo / rel
        repo_paths[rel] = p.exists()
        if not p.exists():
            problems.append(f"missing canonical config: {rel}")

    skill_paths = {}
    for rel in REQUIRED_SKILL_FILES:
        p = skill / rel
        skill_paths[rel] = p.exists()
        if not p.exists():
            problems.append(f"missing bundled skill file: {rel}")

    configs = {stage: config_summary(repo / rel) for stage, rel in CONFIGS.items()}
    for stage, data in configs.items():
        if data.get("exists"):
            if data.get("system_type") != "dreamcraft3d-system":
                warnings.append(f"{stage} config did not report system_type=dreamcraft3d-system")
            if data.get("data_type") != "single-image-datamodule":
                warnings.append(f"{stage} config did not report data_type=single-image-datamodule")

    image_report = image_family(Path(args.image)) if args.image else None
    if image_report and args.require_image_sidecars:
        for key in ("rgba", "depth", "normal"):
            if not image_report[key]["exists"]:
                problems.append(f"required image family member missing: {key} -> {image_report[key]['path']}")

    status = "fail" if problems else "warn" if warnings else "ok"
    return {
        "status": status,
        "repo_root": str(repo),
        "skill_dir": str(skill),
        "repo_paths": repo_paths,
        "skill_paths": skill_paths,
        "configs": configs,
        "image_family": image_report,
        "problems": problems,
        "warnings": warnings,
        "notes": [
            "This checker is static and read-only; it does not prove CUDA training, model loading, or mesh export.",
            "Use sub-skill helpers for deeper image, command, output, texture, or environment-specific checks.",
        ],
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Static DreamCraft3D checkout and generated skill checker.")
    parser.add_argument("--repo-root", default=".", help="DreamCraft3D checkout root to inspect.")
    parser.add_argument("--skill-dir", default=None, help="Generated dreamcraft3d skill directory; defaults to this script's parent skill.")
    parser.add_argument("--image", default=None, help="Optional *_rgba.png image path to check as a sidecar family.")
    parser.add_argument("--require-image-sidecars", action="store_true", help="Fail if --image lacks RGBA/depth/normal family members.")
    parser.add_argument("--json", action="store_true", help="Print JSON.")
    args = parser.parse_args(argv)
    report = check(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"status: {report['status']}")
        for problem in report["problems"]:
            print(f"problem: {problem}")
        for warning in report["warnings"]:
            print(f"warning: {warning}")
        print("configs:")
        for stage, data in report["configs"].items():
            print(f"  {stage}: {data.get('name')} stage={data.get('stage')} renderer={data.get('renderer_type')}")
    return 0 if report["status"] in ("ok", "warn") else 2


if __name__ == "__main__":
    raise SystemExit(main())
