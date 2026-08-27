#!/usr/bin/env python3
"""Construct and inspect tiny offline Krita AI Diffusion WorkflowInput payloads."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any


def find_repo_root(start: Path) -> Path | None:
    for path in [start, *start.parents]:
        if (path / "ai_diffusion" / "__init__.py").exists():
            return path
    return None


def add_local_repo_to_path() -> None:
    for candidate in [Path.cwd(), Path(__file__).resolve().parent]:
        root = find_repo_root(candidate)
        if root is not None:
            root_text = str(root)
            if root_text not in sys.path:
                sys.path.insert(0, root_text)
            return


def parse_extent(value: str):
    from ai_diffusion.image import Extent

    try:
        w, h = value.lower().split("x", 1)
        return Extent(int(w), int(h))
    except Exception as exc:  # noqa: BLE001
        raise argparse.ArgumentTypeError(f"extent must be WIDTHxHEIGHT: {value}") from exc


def parse_bounds(value: str):
    from ai_diffusion.image import Bounds

    try:
        x, y, w, h = (int(part) for part in value.split(","))
        return Bounds(x, y, w, h)
    except Exception as exc:  # noqa: BLE001
        raise argparse.ArgumentTypeError(f"bounds must be x,y,width,height: {value}") from exc


def compact(obj: Any) -> Any:
    from ai_diffusion.image import Bounds, Extent, Image

    if isinstance(obj, Enum):
        return obj.name
    if isinstance(obj, Extent):
        return {"width": obj.width, "height": obj.height}
    if isinstance(obj, Bounds):
        return {"x": obj.x, "y": obj.y, "width": obj.width, "height": obj.height}
    if isinstance(obj, Image):
        return {"width": obj.width, "height": obj.height}
    if is_dataclass(obj):
        return {k: compact(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {str(k): compact(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [compact(v) for v in obj]
    return obj


def make_common(extent, target, prompt: str, seed: int):
    from ai_diffusion.backend.api import CheckpointInput, ConditioningInput, ImageInput, SamplingInput
    from ai_diffusion.backend.resources import Arch

    images = ImageInput.from_extent(extent)
    images.extent = images.extent.__class__(extent, extent, target, target)
    models = CheckpointInput("example-sd15.safetensors", Arch.sd15)
    sampling = SamplingInput("dpmpp_2m_sde_gpu", "normal", 7.0, 20, seed=seed)
    conditioning = ConditioningInput(prompt)
    return images, models, sampling, conditioning


def make_workflow(args):
    from ai_diffusion.backend.api import InpaintMode, InpaintParams, UpscaleInput, WorkflowInput, WorkflowKind
    from ai_diffusion.image import Image

    extent = args.extent
    target = args.target or extent
    images, models, sampling, conditioning = make_common(extent, target, args.prompt, args.seed)
    kind_name = args.kind.replace("-", "_")
    kind = WorkflowKind[kind_name]

    if kind in {WorkflowKind.refine, WorkflowKind.inpaint, WorkflowKind.upscale_simple, WorkflowKind.upscale_tiled}:
        images.initial_image = Image.create(extent)
    if kind is WorkflowKind.inpaint:
        images.hires_mask = Image.create(extent)
        inpaint = InpaintParams(InpaintMode.fill, args.target_bounds)
        inpaint.fill = inpaint.fill.__class__.blur
        inpaint.grow = 12
        inpaint.feather = 24
        inpaint.blend = 12
        inpaint.use_inpaint_model = True
        inpaint.use_reference = True
    else:
        inpaint = None

    upscale = None
    if kind is WorkflowKind.upscale_simple:
        upscale = UpscaleInput(model=args.upscaler)
    elif kind is WorkflowKind.upscale_tiled:
        upscale = UpscaleInput(model=args.upscaler, tile_overlap=args.tile_overlap)

    return WorkflowInput(
        kind=kind,
        images=images,
        models=models if kind is not WorkflowKind.control_image else None,
        sampling=sampling if kind is not WorkflowKind.control_image else None,
        conditioning=conditioning,
        inpaint=inpaint,
        upscale=upscale,
        batch_count=args.batch_count,
    )


def summarize(work) -> dict[str, Any]:
    data = {
        "kind": work.kind.name,
        "has_image_data": False,
        "extent": compact(work.images.extent if work.images else None),
        "images": {
            "initial_image": compact(work.images.initial_image) if work.images else None,
            "hires_image": compact(work.images.hires_image) if work.images else None,
            "hires_mask": compact(work.images.hires_mask) if work.images else None,
            "layer_count": work.images.layer_count if work.images else None,
        },
        "models": compact(work.models),
        "sampling": compact(work.sampling),
        "conditioning": compact(work.conditioning),
        "inpaint": compact(work.inpaint),
        "upscale": compact(work.upscale),
        "passes_count": work.passes_count,
    }
    try:
        data["cost"] = work.cost
    except Exception as exc:  # noqa: BLE001
        data["cost_error"] = f"{type(exc).__name__}: {exc}"
    return data


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Construct and inspect tiny offline WorkflowInput payloads.")
    parser.add_argument("--kind", default="generate", choices=["generate", "refine", "inpaint", "upscale-simple", "upscale-tiled", "control-image", "custom"], help="Workflow kind to construct.")
    parser.add_argument("--extent", default="512x512", help="Input extent WIDTHxHEIGHT.")
    parser.add_argument("--target", help="Target extent WIDTHxHEIGHT.")
    parser.add_argument("--target-bounds", default="128,96,192,160", help="Inpaint target bounds x,y,width,height.")
    parser.add_argument("--prompt", default="a lighthouse on the beach")
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--batch-count", type=int, default=1)
    parser.add_argument("--upscaler", default="4x_NMKD-Siax_200k.pth")
    parser.add_argument("--tile-overlap", type=int, default=-1)
    parser.add_argument("--round-trip", action="store_true", help="Serialize with PNG image data and deserialize.")
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    add_local_repo_to_path()
    args = parser.parse_args(argv)
    args.extent = parse_extent(args.extent)
    args.target = parse_extent(args.target) if args.target else None
    args.target_bounds = parse_bounds(args.target_bounds)

    work = make_workflow(args)
    info = summarize(work)
    if args.round_trip:
        from ai_diffusion.backend.api import WorkflowInput
        from ai_diffusion.settings import ImageFileFormat

        serialized = work.to_dict(image_format=ImageFileFormat.png)
        info["serialized_keys"] = sorted(serialized.keys())
        info["has_image_data"] = "image_data" in serialized
        if "image_data" in serialized:
            image_data = serialized["image_data"]
            info["image_data_summary"] = {
                "byte_count": len(image_data.get("bytes", b"")),
                "offset_count": len(image_data.get("offsets", [])),
            }
        back = WorkflowInput.from_dict(serialized)
        info["round_trip"] = "ok" if back.kind is work.kind else f"kind changed to {back.kind.name}"

    if args.json:
        print(json.dumps(info, indent=2, sort_keys=True))
    else:
        for key, value in info.items():
            if isinstance(value, (dict, list)):
                print(f"{key}: {json.dumps(value, sort_keys=True)}")
            else:
                print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
