#!/usr/bin/env python3
"""Generate a Hunyuan3D shape from one image or a multiview image set.

The script is intentionally safe for skill verification: heavy Hunyuan3D imports
and model downloads happen only when --dry-run is not supplied.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional

VALID_VIEWS = ("front", "back", "left", "right")

MODEL_PRESETS = {
    "base": ("tencent/Hunyuan3D-2", "hunyuan3d-dit-v2-0"),
    "base-fast": ("tencent/Hunyuan3D-2", "hunyuan3d-dit-v2-0-fast"),
    "base-turbo": ("tencent/Hunyuan3D-2", "hunyuan3d-dit-v2-0-turbo"),
    "mini": ("tencent/Hunyuan3D-2mini", "hunyuan3d-dit-v2-mini"),
    "mini-fast": ("tencent/Hunyuan3D-2mini", "hunyuan3d-dit-v2-mini-fast"),
    "mini-turbo": ("tencent/Hunyuan3D-2mini", "hunyuan3d-dit-v2-mini-turbo"),
    "mv": ("tencent/Hunyuan3D-2mv", "hunyuan3d-dit-v2-mv"),
    "mv-fast": ("tencent/Hunyuan3D-2mv", "hunyuan3d-dit-v2-mv-fast"),
    "mv-turbo": ("tencent/Hunyuan3D-2mv", "hunyuan3d-dit-v2-mv-turbo"),
    "v2.1": ("tencent/Hunyuan3D-2.1", "hunyuan3d-dit-v2-1"),
}


def _existing_file(value: Optional[str], label: str) -> Optional[str]:
    if value is None:
        return None
    path = Path(value).expanduser()
    if not path.is_file():
        raise SystemExit(f"{label} does not exist or is not a file: {value}")
    return str(path)


def parse_view_specs(specs: Optional[List[str]]) -> Dict[str, str]:
    views: Dict[str, str] = {}
    for spec in specs or []:
        if "=" not in spec:
            raise SystemExit("--view values must be VIEW=PATH, for example --view front=front.png")
        view, value = spec.split("=", 1)
        view = view.strip().lower()
        if view not in VALID_VIEWS:
            raise SystemExit(f"Unsupported view {view!r}; valid views are {', '.join(VALID_VIEWS)}")
        views[view] = _existing_file(value, f"--view {view}") or value
    return views


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run or dry-run Hunyuan3D-DiT shape generation.")
    parser.add_argument("--preset", choices=sorted(MODEL_PRESETS), default="base", help="Model/subfolder preset.")
    parser.add_argument("--model-path", help="Override Hugging Face repo id or local model directory.")
    parser.add_argument("--subfolder", help="Override model subfolder.")
    parser.add_argument("--image", help="Single input image path for image-to-shape.")
    parser.add_argument("--view", action="append", help="Multiview input as VIEW=PATH; valid views: front, back, left, right.")
    parser.add_argument("--output", default="mesh.glb", help="Output mesh path for a full run.")
    parser.add_argument("--device", default="cuda", help="Torch device; actual generation is expected to use cuda.")
    parser.add_argument("--variant", default="fp16", help="Checkpoint variant passed to from_pretrained; use 'none' for None.")
    parser.add_argument("--dtype", default="float16", choices=["float16", "float32", "bfloat16"], help="Torch dtype.")
    parser.add_argument("--steps", type=int, default=50, help="Number of diffusion steps.")
    parser.add_argument("--guidance-scale", type=float, default=5.0, help="Classifier-free guidance scale.")
    parser.add_argument("--octree-resolution", type=int, default=384, help="Surface extraction resolution.")
    parser.add_argument("--num-chunks", type=int, default=8000, help="Chunk size used while exporting latents to mesh.")
    parser.add_argument("--seed", type=int, default=12345, help="Random seed.")
    parser.add_argument("--mc-algo", default=None, help="Marching-cubes backend, for example mc when FlashVDM is enabled.")
    parser.add_argument("--enable-flashvdm", action="store_true", help="Enable FlashVDM decoder before sampling.")
    parser.add_argument("--skip-rembg", action="store_true", help="Do not run BackgroundRemover on RGB inputs.")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and print the execution plan without importing models.")
    return parser


def make_plan(args: argparse.Namespace) -> dict:
    model_path, subfolder = MODEL_PRESETS[args.preset]
    model_path = args.model_path or model_path
    subfolder = args.subfolder or subfolder

    views = parse_view_specs(args.view)
    single_image = _existing_file(args.image, "--image") if args.image else None
    if bool(single_image) == bool(views):
        raise SystemExit("Provide exactly one input mode: --image PATH or one or more --view VIEW=PATH entries.")
    if views and not ("mv" in model_path.lower() or "mv" in subfolder.lower()):
        raise SystemExit("Multiview inputs require an mv model, for example --preset mv or --preset mv-turbo.")
    if args.steps <= 0:
        raise SystemExit("--steps must be positive")
    if args.octree_resolution <= 0:
        raise SystemExit("--octree-resolution must be positive")
    if args.num_chunks <= 0:
        raise SystemExit("--num-chunks must be positive")

    return {
        "model_path": model_path,
        "subfolder": subfolder,
        "input_mode": "multiview" if views else "single-image",
        "image": single_image,
        "views": views,
        "output": args.output,
        "device": args.device,
        "dtype": args.dtype,
        "variant": None if args.variant.lower() == "none" else args.variant,
        "steps": args.steps,
        "guidance_scale": args.guidance_scale,
        "octree_resolution": args.octree_resolution,
        "num_chunks": args.num_chunks,
        "seed": args.seed,
        "enable_flashvdm": args.enable_flashvdm,
        "mc_algo": args.mc_algo,
        "skip_rembg": args.skip_rembg,
    }


def run(plan: dict) -> None:
    import torch
    from PIL import Image

    from hy3dgen.rembg import BackgroundRemover
    from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

    dtype = getattr(torch, plan["dtype"])
    if plan["input_mode"] == "single-image":
        raw = Image.open(plan["image"])
        if not plan["skip_rembg"] and raw.mode == "RGB":
            image = BackgroundRemover()(raw)
        else:
            image = raw.convert("RGBA")
    else:
        image = {}
        rembg = None if plan["skip_rembg"] else BackgroundRemover()
        for view, value in plan["views"].items():
            raw = Image.open(value)
            if rembg is not None and raw.mode == "RGB":
                img = rembg(raw)
            else:
                img = raw.convert("RGBA")
            image[view] = img

    pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
        plan["model_path"],
        device=plan["device"],
        dtype=dtype,
        use_safetensors=True,
        variant=plan["variant"],
        subfolder=plan["subfolder"],
    )
    if plan["enable_flashvdm"]:
        pipeline.enable_flashvdm(mc_algo=plan["mc_algo"] or "mc")

    generator = torch.Generator(device=plan["device"]).manual_seed(plan["seed"])
    mesh = pipeline(
        image=image,
        num_inference_steps=plan["steps"],
        guidance_scale=plan["guidance_scale"],
        generator=generator,
        octree_resolution=plan["octree_resolution"],
        num_chunks=plan["num_chunks"],
        mc_algo=plan["mc_algo"],
        output_type="trimesh",
    )[0]
    Path(plan["output"]).expanduser().parent.mkdir(parents=True, exist_ok=True)
    mesh.export(plan["output"])
    print(f"exported {plan['output']}")


def main() -> None:
    args = build_parser().parse_args()
    plan = make_plan(args)
    if args.dry_run:
        print(json.dumps({"status": "dry-run", "plan": plan}, indent=2, sort_keys=True))
        return
    if plan["device"] == "cpu":
        raise SystemExit("Hunyuan3D generation is not verified as a CPU workflow; use a CUDA environment for real runs.")
    run(plan)


if __name__ == "__main__":
    main()
