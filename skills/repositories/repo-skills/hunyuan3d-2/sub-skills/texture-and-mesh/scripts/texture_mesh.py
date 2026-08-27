#!/usr/bin/env python3
"""Texture an existing or newly generated mesh with Hunyuan3D-Paint.

Heavy imports, CUDA extension loading, and model downloads happen only outside
--dry-run so this script can be used in static skill verification.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Optional

SHAPE_PRESETS = {
    "base": ("tencent/Hunyuan3D-2", "hunyuan3d-dit-v2-0"),
    "base-turbo": ("tencent/Hunyuan3D-2", "hunyuan3d-dit-v2-0-turbo"),
    "mini": ("tencent/Hunyuan3D-2mini", "hunyuan3d-dit-v2-mini"),
    "mini-turbo": ("tencent/Hunyuan3D-2mini", "hunyuan3d-dit-v2-mini-turbo"),
    "mv": ("tencent/Hunyuan3D-2mv", "hunyuan3d-dit-v2-mv"),
    "mv-turbo": ("tencent/Hunyuan3D-2mv", "hunyuan3d-dit-v2-mv-turbo"),
}


def existing_file(value: Optional[str], label: str) -> Optional[str]:
    if value is None:
        return None
    path = Path(value).expanduser()
    if not path.is_file():
        raise SystemExit(f"{label} does not exist or is not a file: {value}")
    return str(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run or dry-run Hunyuan3D-Paint mesh texturing.")
    parser.add_argument("--mesh", help="Existing mesh path to texture; GLB is the most common input.")
    parser.add_argument("--shape-image", help="Generate a white mesh from this image before texturing when --mesh is omitted.")
    parser.add_argument("--image", action="append", help="Texture conditioning image path. Repeat for multiview texture prompts.")
    parser.add_argument("--output", default="textured_mesh.glb", help="Output textured mesh path.")
    parser.add_argument("--paint-model-path", default="tencent/Hunyuan3D-2", help="Paint model repo id or local model directory.")
    parser.add_argument("--paint-subfolder", default="hunyuan3d-paint-v2-0-turbo", choices=["hunyuan3d-paint-v2-0", "hunyuan3d-paint-v2-0-turbo"], help="Paint model subfolder.")
    parser.add_argument("--shape-preset", choices=sorted(SHAPE_PRESETS), default="base-turbo", help="Shape model preset used only with --shape-image.")
    parser.add_argument("--shape-steps", type=int, default=5, help="Shape sampling steps used only with --shape-image.")
    parser.add_argument("--shape-octree-resolution", type=int, default=384, help="Shape octree resolution used only with --shape-image.")
    parser.add_argument("--shape-num-chunks", type=int, default=200000, help="Shape export chunks used only with --shape-image.")
    parser.add_argument("--seed", type=int, default=12345, help="Shape generation seed when --shape-image is used.")
    parser.add_argument("--device", default="cuda", help="Shape-generation device; paint pipeline is CUDA-oriented in this repo.")
    parser.add_argument("--enable-flashvdm", action="store_true", help="Enable FlashVDM for generated shape path.")
    parser.add_argument("--skip-rembg", action="store_true", help="Do not run BackgroundRemover on RGB images.")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and print a plan without importing models.")
    return parser


def make_plan(args: argparse.Namespace) -> dict:
    mesh = existing_file(args.mesh, "--mesh") if args.mesh else None
    shape_image = existing_file(args.shape_image, "--shape-image") if args.shape_image else None
    if mesh is None and shape_image is None:
        raise SystemExit("Provide --mesh for existing-mesh texturing or --shape-image to generate a mesh first.")
    if mesh is not None and shape_image is not None:
        raise SystemExit("Use either --mesh or --shape-image, not both.")
    images: List[str] = [existing_file(v, "--image") or v for v in (args.image or [])]
    if not images and shape_image:
        images = [shape_image]
    if not images:
        raise SystemExit("Provide at least one --image for texture conditioning.")
    if args.shape_steps <= 0 or args.shape_octree_resolution <= 0 or args.shape_num_chunks <= 0:
        raise SystemExit("Shape step/resolution/chunk values must be positive.")
    shape_model_path, shape_subfolder = SHAPE_PRESETS[args.shape_preset]
    return {
        "mode": "existing-mesh" if mesh else "generate-then-texture",
        "mesh": mesh,
        "shape_image": shape_image,
        "texture_images": images,
        "output": args.output,
        "paint_model_path": args.paint_model_path,
        "paint_subfolder": args.paint_subfolder,
        "shape_model_path": shape_model_path,
        "shape_subfolder": shape_subfolder,
        "shape_steps": args.shape_steps,
        "shape_octree_resolution": args.shape_octree_resolution,
        "shape_num_chunks": args.shape_num_chunks,
        "seed": args.seed,
        "device": args.device,
        "enable_flashvdm": args.enable_flashvdm,
        "skip_rembg": args.skip_rembg,
    }


def load_image(path: str, skip_rembg: bool):
    from PIL import Image
    from hy3dgen.rembg import BackgroundRemover

    raw = Image.open(path)
    if not skip_rembg and raw.mode == "RGB":
        return BackgroundRemover()(raw)
    return raw.convert("RGBA")


def run(plan: dict) -> None:
    # Import torch before custom_rasterizer-backed texgen modules so libc10 is loaded.
    import torch
    import trimesh

    from hy3dgen.texgen import Hunyuan3DPaintPipeline

    if plan["mode"] == "existing-mesh":
        mesh = trimesh.load(plan["mesh"])
    else:
        from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

        shape_image = load_image(plan["shape_image"], plan["skip_rembg"])
        shape_pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
            plan["shape_model_path"],
            subfolder=plan["shape_subfolder"],
            use_safetensors=True,
            device=plan["device"],
        )
        if plan["enable_flashvdm"]:
            shape_pipeline.enable_flashvdm(mc_algo="mc")
        mesh = shape_pipeline(
            image=shape_image,
            num_inference_steps=plan["shape_steps"],
            octree_resolution=plan["shape_octree_resolution"],
            num_chunks=plan["shape_num_chunks"],
            generator=torch.Generator(plan["device"]).manual_seed(plan["seed"]),
            output_type="trimesh",
        )[0]

    images = [load_image(path, plan["skip_rembg"]) for path in plan["texture_images"]]
    image_arg = images[0] if len(images) == 1 else images
    paint = Hunyuan3DPaintPipeline.from_pretrained(plan["paint_model_path"], subfolder=plan["paint_subfolder"])
    textured = paint(mesh, image=image_arg)
    Path(plan["output"]).expanduser().parent.mkdir(parents=True, exist_ok=True)
    textured.export(plan["output"])
    print(f"exported {plan['output']}")


def main() -> None:
    args = build_parser().parse_args()
    plan = make_plan(args)
    if args.dry_run:
        print(json.dumps({"status": "dry-run", "plan": plan}, indent=2, sort_keys=True))
        return
    if plan["device"] == "cpu":
        raise SystemExit("Texture generation is CUDA-oriented and was not verified as a CPU workflow.")
    run(plan)


if __name__ == "__main__":
    main()
