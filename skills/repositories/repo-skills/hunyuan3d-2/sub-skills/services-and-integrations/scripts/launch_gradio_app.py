#!/usr/bin/env python3
"""Compact self-contained Gradio launcher for Hunyuan3D-2.

This is not a byte-for-byte copy of the upstream demo; it provides a portable
single-image generation UI that works from the skill tree with installed
Hunyuan3D packages and model weights.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch a compact Hunyuan3D-2 Gradio app.")
    parser.add_argument("--model-path", default="tencent/Hunyuan3D-2mini", help="Shape model repo id or local path.")
    parser.add_argument("--subfolder", default="hunyuan3d-dit-v2-mini-turbo", help="Shape model subfolder.")
    parser.add_argument("--texgen-model-path", default="tencent/Hunyuan3D-2", help="Texture model repo id or local path.")
    parser.add_argument("--texgen-subfolder", default="hunyuan3d-paint-v2-0-turbo", help="Texture model subfolder.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host.")
    parser.add_argument("--port", type=int, default=8080, help="Bind port.")
    parser.add_argument("--device", default="cuda", help="Torch device.")
    parser.add_argument("--cache-path", default="hunyuan3d_gradio_cache", help="Directory for generated meshes.")
    parser.add_argument("--enable-tex", action="store_true", help="Load paint pipeline and expose texture option.")
    parser.add_argument("--enable-flashvdm", action="store_true", help="Enable FlashVDM decoder.")
    parser.add_argument("--mc-algo", default="mc", help="Marching-cubes backend.")
    parser.add_argument("--low-vram-mode", action="store_true", help="Enable paint model CPU offload when texture is enabled.")
    parser.add_argument("--share", action="store_true", help="Pass share=True to Gradio launch.")
    parser.add_argument("--dry-run", action="store_true", help="Print launch plan without importing models or starting Gradio.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    plan = vars(args).copy()
    if args.dry_run:
        print(json.dumps({"status": "dry-run", "plan": plan}, indent=2, sort_keys=True))
        return
    if args.device == "cpu":
        raise SystemExit("Real Hunyuan3D generation is CUDA-scoped in this skill; use --device cuda.")

    import tempfile
    import time

    import gradio as gr
    import torch
    from PIL import Image

    from hy3dgen.rembg import BackgroundRemover
    from hy3dgen.shapegen import DegenerateFaceRemover, FaceReducer, FloaterRemover, Hunyuan3DDiTFlowMatchingPipeline
    from hy3dgen.texgen import Hunyuan3DPaintPipeline

    cache_dir = Path(args.cache_path)
    cache_dir.mkdir(parents=True, exist_ok=True)

    rembg = BackgroundRemover()
    shape = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
        args.model_path,
        subfolder=args.subfolder,
        use_safetensors=True,
        device=args.device,
    )
    if args.enable_flashvdm:
        shape.enable_flashvdm(mc_algo=args.mc_algo)

    paint = None
    if args.enable_tex:
        paint = Hunyuan3DPaintPipeline.from_pretrained(args.texgen_model_path, subfolder=args.texgen_subfolder)
        if args.low_vram_mode:
            paint.enable_model_cpu_offload(device=args.device)

    def generate(image: Image.Image, steps: int, guidance_scale: float, octree_resolution: int, seed: int, texture: bool, remove_background: bool):
        if image is None:
            raise gr.Error("Upload an input image.")
        if texture and paint is None:
            raise gr.Error("Texture was requested, but the app was launched without --enable-tex.")
        pil = image.convert("RGBA")
        if remove_background:
            pil = rembg(pil.convert("RGB"))
        started = time.time()
        generator = torch.Generator(args.device).manual_seed(int(seed))
        mesh = shape(
            image=pil,
            num_inference_steps=int(steps),
            guidance_scale=float(guidance_scale),
            generator=generator,
            octree_resolution=int(octree_resolution),
            mc_algo=args.mc_algo,
            output_type="trimesh",
        )[0]
        if texture:
            mesh = FloaterRemover()(mesh)
            mesh = DegenerateFaceRemover()(mesh)
            mesh = FaceReducer()(mesh, max_facenum=40000)
            mesh = paint(mesh, image=pil)
        with tempfile.NamedTemporaryFile(prefix="hunyuan3d_", suffix=".glb", dir=str(cache_dir), delete=False) as tmp:
            mesh.export(tmp.name)
            output_path = tmp.name
        torch.cuda.empty_cache()
        stats = {
            "seconds": round(time.time() - started, 3),
            "model": f"{args.model_path}/{args.subfolder}",
            "texture": bool(texture),
            "seed": int(seed),
            "steps": int(steps),
            "guidance_scale": float(guidance_scale),
            "octree_resolution": int(octree_resolution),
            "output": output_path,
        }
        return output_path, json.dumps(stats, indent=2)

    with gr.Blocks(title="Hunyuan3D-2 Compact") as demo:
        gr.Markdown("# Hunyuan3D-2 Compact Gradio App\nUpload one image and generate a GLB mesh. Texture requires launching with `--enable-tex`.")
        with gr.Row():
            image = gr.Image(label="Input image", type="pil")
            model = gr.Model3D(label="Output GLB")
        with gr.Row():
            steps = gr.Slider(1, 50, value=5 if "turbo" in args.subfolder else 30, step=1, label="Steps")
            guidance = gr.Slider(1.0, 10.0, value=5.0, step=0.1, label="Guidance scale")
            octree = gr.Slider(128, 512, value=256, step=64, label="Octree resolution")
            seed = gr.Number(value=12345, precision=0, label="Seed")
        with gr.Row():
            texture = gr.Checkbox(value=False, label="Generate texture")
            remove_background = gr.Checkbox(value=True, label="Remove background")
        run = gr.Button("Generate")
        stats = gr.Code(label="Stats", language="json")
        run.click(generate, inputs=[image, steps, guidance, octree, seed, texture, remove_background], outputs=[model, stats])

    demo.launch(server_name=args.host, server_port=args.port, share=args.share)


if __name__ == "__main__":
    main()
