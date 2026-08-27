#!/usr/bin/env python3
"""Build DreamCraft3D staged commands without executing training."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

STAGES = [
    {
        "id": "coarse_nerf",
        "label": "Stage 1A coarse NeRF",
        "config": "configs/dreamcraft3d-coarse-nerf.yaml",
        "output_name": "dreamcraft3d-coarse-nerf",
        "mode": "--train",
        "requires": [],
    },
    {
        "id": "coarse_neus",
        "label": "Stage 1B coarse NeuS",
        "config": "configs/dreamcraft3d-coarse-neus.yaml",
        "output_name": "dreamcraft3d-coarse-neus",
        "mode": "--train",
        "requires": ["system.weights"],
    },
    {
        "id": "geometry",
        "label": "Stage 2 geometry refinement",
        "config": "configs/dreamcraft3d-geometry.yaml",
        "output_name": "dreamcraft3d-geometry",
        "mode": "--train",
        "requires": ["system.geometry_convert_from"],
    },
    {
        "id": "texture",
        "label": "Stage 3 texture refinement",
        "config": "configs/dreamcraft3d-texture.yaml",
        "output_name": "dreamcraft3d-texture",
        "mode": "--train",
        "requires": ["system.geometry_convert_from"],
    },
]


def prompt_tag(prompt: str) -> str:
    return re.sub(r"\s+", "_", prompt.strip()) or "prompt"


def q(value: str) -> str:
    return shlex.quote(str(value))


def ckpt_path(output_root: str, output_name: str, tag: str) -> str:
    return str(Path(output_root) / output_name / f"{tag}@LAST" / "ckpts" / "last.ckpt")


def build(args: argparse.Namespace) -> Dict[str, Any]:
    problems: List[str] = []
    if not args.prompt.strip():
        problems.append("--prompt must be non-empty")
    if not args.image_path.strip():
        problems.append("--image-path must be non-empty")

    tag = prompt_tag(args.prompt)
    inferred = {
        "coarse_nerf_ckpt": args.coarse_nerf_ckpt or ckpt_path(args.output_root, "dreamcraft3d-coarse-nerf", tag),
        "coarse_neus_ckpt": args.coarse_neus_ckpt or ckpt_path(args.output_root, "dreamcraft3d-coarse-neus", tag),
        "geometry_ckpt": args.geometry_ckpt or ckpt_path(args.output_root, "dreamcraft3d-geometry", tag),
        "texture_ckpt": ckpt_path(args.output_root, "dreamcraft3d-texture", tag),
    }

    commands: List[Dict[str, Any]] = []
    prev_ckpts = {
        "coarse_neus": inferred["coarse_nerf_ckpt"],
        "geometry": inferred["coarse_neus_ckpt"],
        "texture": inferred["geometry_ckpt"],
    }
    override_key = {
        "coarse_neus": "system.weights",
        "geometry": "system.geometry_convert_from",
        "texture": "system.geometry_convert_from",
    }

    for stage in STAGES:
        parts = [
            "python",
            "launch.py",
            "--config",
            stage["config"],
            stage["mode"],
            "--gpu",
            args.gpu,
            f"system.prompt_processor.prompt={args.prompt}",
            f"data.image_path={args.image_path}",
        ]
        notes = []
        if stage["id"] in prev_ckpts:
            parts.append(f"{override_key[stage['id']]}={prev_ckpts[stage['id']]}")
            notes.append(f"requires prior checkpoint: {prev_ckpts[stage['id']]}")
        command = " ".join(q(p) for p in parts)
        commands.append(
            {
                "id": stage["id"],
                "label": stage["label"],
                "config": stage["config"],
                "command": command,
                "expected_checkpoint": inferred.get(f"{stage['id']}_ckpt", ckpt_path(args.output_root, stage["output_name"], tag)),
                "notes": notes,
            }
        )

    export_parts = [
        "python",
        "launch.py",
        "--config",
        str(Path(args.output_root) / "dreamcraft3d-texture" / f"{tag}@LAST" / "configs" / "parsed.yaml"),
        "--export",
        "--gpu",
        args.gpu,
        f"resume={inferred['texture_ckpt']}",
        "system.exporter_type=mesh-exporter",
    ]
    commands.append(
        {
            "id": "export_mesh",
            "label": "Export textured mesh",
            "config": "<texture-trial>/configs/parsed.yaml",
            "command": " ".join(q(p) for p in export_parts),
            "expected_checkpoint": None,
            "notes": ["requires completed texture checkpoint and CUDA/nvdiffrast exporter"],
        }
    )

    return {
        "status": "fail" if problems else "ok",
        "prompt": args.prompt,
        "prompt_tag": tag,
        "image_path": args.image_path,
        "gpu": args.gpu,
        "output_root": args.output_root,
        "problems": problems,
        "commands": commands,
        "warnings": [
            "Commands are generated only; this script does not execute DreamCraft3D.",
            "Full stages require CUDA, large model artifacts, and significant runtime.",
            "Verify image sidecars and prior checkpoints before executing each command.",
        ],
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build DreamCraft3D stage commands without running them.")
    parser.add_argument("--prompt", required=True, help="Text prompt passed to system.prompt_processor.prompt.")
    parser.add_argument("--image-path", required=True, help="Repo-relative or absolute path to a *_rgba.png image.")
    parser.add_argument("--gpu", default="0", help="GPU ids for launch.py --gpu; ignored by launch.py if CUDA_VISIBLE_DEVICES is already set.")
    parser.add_argument("--output-root", default="outputs", help="Expected DreamCraft3D output root.")
    parser.add_argument("--coarse-nerf-ckpt", default=None, help="Override inferred coarse NeRF checkpoint path.")
    parser.add_argument("--coarse-neus-ckpt", default=None, help="Override inferred coarse NeuS checkpoint path.")
    parser.add_argument("--geometry-ckpt", default=None, help="Override inferred geometry checkpoint path.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    report = build(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"status: {report['status']}")
        for problem in report["problems"]:
            print(f"problem: {problem}")
        for item in report["commands"]:
            print(f"\n# {item['label']} ({item['id']})")
            for note in item["notes"]:
                print(f"# note: {note}")
            print(item["command"])
    return 0 if report["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
