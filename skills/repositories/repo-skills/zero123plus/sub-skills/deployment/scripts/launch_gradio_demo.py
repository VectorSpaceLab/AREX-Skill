#!/usr/bin/env python3
"""Minimal Zero123Plus Gradio launcher/template.

This script is a clean-room deployment wrapper derived from the repo's Gradio
surface. It intentionally avoids importing the source UI modules, does not load
models on import, and keeps network downloads opt-in via --allow-download.

The detailed multiview generation workflow belongs to the sibling generation
sub-skill; this launcher only owns a small upload -> generate -> six-view gallery
loop so future agents can adapt serving behavior safely.
"""
from __future__ import annotations

import argparse
import importlib.util
import shutil
import sys
from pathlib import Path
from typing import Iterable, Optional

DEFAULT_MODEL_ID = "sudo-ai/zero123plus-v1.1"
DEFAULT_CUSTOM_PIPELINE = "sudo-ai/zero123plus-pipeline"

REQUIRED_MODULES = {
    "torch": "pip install torch torchvision",
    "diffusers": "pip install diffusers==0.20.2 transformers==4.29.2",
    "gradio": "pip install gradio>=3.50",
    "PIL": "pip install pillow",
}

OPTIONAL_SOURCE_DEMO_MODULES = {
    "rembg": "used by the full source demos for background removal",
    "segment_anything": "used by the full source demos for SAM mask refinement",
    "streamlit": "used by the source Streamlit demo",
}


def _has_module(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _require_module(module_name: str, install_hint: str) -> None:
    if not _has_module(module_name):
        raise ImportError(
            f"Missing required dependency '{module_name}'. Install it with: {install_hint}"
        )


def _python_resample():
    from PIL import Image

    return getattr(Image, "Resampling", Image)


def _expand2square(image, background_color):
    from PIL import Image

    width, height = image.size
    if width == height:
        return image
    if width > height:
        result = Image.new(image.mode, (width, width), background_color)
        result.paste(image, (0, (width - height) // 2))
        return result
    result = Image.new(image.mode, (height, height), background_color)
    result.paste(image, ((height - width) // 2, 0))
    return result


def _prepare_input_image(image):
    from PIL import Image

    if image.mode not in {"RGB", "RGBA"}:
        image = image.convert("RGB")
    if max(image.size) > 1280:
        width, height = image.size
        scale = 1280 / float(max(image.size))
        image = image.resize((round(width * scale), round(height * scale)), _python_resample().LANCZOS)
    image = _expand2square(image.convert("RGB"), (127, 127, 127))
    return image


def _split_views(grid_image):
    width = grid_image.width // 2
    height = grid_image.height // 3
    tiles = []
    for row in range(3):
        for col in range(2):
            left = col * width
            top = row * height
            tiles.append(grid_image.crop((left, top, left + width, top + height)))
    return tiles


def _check_environment() -> bool:
    ready = True
    print("Zero123Plus minimal Gradio launcher environment check")
    for module_name, install_hint in REQUIRED_MODULES.items():
        if module_name == "PIL":
            exists = _has_module("PIL")
        else:
            exists = _has_module(module_name)
        status = "ok" if exists else "missing"
        print(f"- {module_name}: {status}")
        if not exists:
            print(f"  install hint: {install_hint}")
            ready = False

    if _has_module("torch"):
        import torch

        cuda_status = torch.cuda.is_available()
        print(f"- CUDA: {'available' if cuda_status else 'missing'}")
        if not cuda_status:
            print("  install hint: use a CUDA-enabled PyTorch build and a GPU runtime")
            ready = False
    else:
        print("- CUDA: cannot check because torch is missing")
        ready = False

    for module_name, note in OPTIONAL_SOURCE_DEMO_MODULES.items():
        status = "ok" if _has_module(module_name) else "missing"
        print(f"- optional {module_name}: {status} ({note})")

    pget_path = shutil.which("pget")
    print(f"- pget: {'ok' if pget_path else 'missing'}")
    if not pget_path:
        print("  install hint: required only for the Cog weight-archive setup path")

    return ready


def _load_pipeline(model_id: str, allow_download: bool):
    _require_module("torch", REQUIRED_MODULES["torch"])
    _require_module("diffusers", REQUIRED_MODULES["diffusers"])

    import torch

    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is required for this demo launcher. The source Zero123Plus demo \
uses a CUDA float16 pipeline and is not intended for CPU-only deployment."
        )

    from diffusers import DiffusionPipeline, EulerAncestralDiscreteScheduler

    try:
        pipeline = DiffusionPipeline.from_pretrained(
            model_id,
            custom_pipeline=DEFAULT_CUSTOM_PIPELINE,
            torch_dtype=torch.float16,
            local_files_only=not allow_download,
        )
    except Exception as exc:
        if not allow_download:
            raise RuntimeError(
                f"Could not load '{model_id}' from local cache. Downloads are disabled by \
default; pre-populate the cache or rerun with --allow-download after network \
access is approved."
            ) from exc
        raise

    pipeline.scheduler = EulerAncestralDiscreteScheduler.from_config(
        pipeline.scheduler.config,
        timestep_spacing="trailing",
    )
    pipeline.to("cuda:0")
    return pipeline


def _build_demo(pipeline):
    _require_module("gradio", REQUIRED_MODULES["gradio"])
    import gradio as gr
    import torch

    def generate(image, steps, guidance_scale, seed):
        if image is None:
            raise ValueError("Upload an image before generating views.")
        prepared = _prepare_input_image(image)
        seed_value = int(seed)
        generator = torch.Generator(device=pipeline.device).manual_seed(seed_value)
        output = pipeline(
            prepared,
            num_inference_steps=int(steps),
            guidance_scale=float(guidance_scale),
            generator=generator,
        ).images[0]
        return _split_views(output)

    with gr.Blocks(title="Zero123Plus demo launcher") as demo:
        gr.Markdown(
            "# Zero123Plus demo launcher\n\n"
            "This standalone launcher mirrors the source Gradio surface without \
importing the original demo modules. For the full image-to-multiview workflow, \
see the sibling generation sub-skill."
        )
        with gr.Row():
            input_image = gr.Image(type="pil", image_mode="RGB", label="Input image")
        with gr.Row():
            steps = gr.Slider(15, 100, value=75, step=1, label="Number of inference steps")
            guidance_scale = gr.Slider(1.0, 10.0, value=4.0, step=0.1, label="Guidance scale")
        seed = gr.Number(value=42, label="Seed", precision=0)
        run_button = gr.Button("Generate", variant="primary")
        output_gallery = gr.Gallery(label="Six-view output", columns=3, height=640)

        run_button.click(
            fn=generate,
            inputs=[input_image, steps, guidance_scale, seed],
            outputs=[output_gallery],
        )

    return demo


def parse_args(argv: Optional[Iterable[str]] = None):
    parser = argparse.ArgumentParser(
        description="Launch a safe, self-contained Zero123Plus Gradio demo."
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host/IP passed to Gradio as server_name.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port passed to Gradio as server_port.",
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Request a public Gradio share tunnel.",
    )
    parser.add_argument(
        "--model-id",
        default=DEFAULT_MODEL_ID,
        help="Diffusers model id or local directory to load.",
    )
    parser.add_argument(
        "--allow-download",
        action="store_true",
        help="Allow model/custom-pipeline downloads instead of local-only loading.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Check dependencies and CUDA without starting Gradio or loading a model.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    if args.check_only:
        ok = _check_environment()
        return 0 if ok else 1

    _require_module("gradio", REQUIRED_MODULES["gradio"])
    pipeline = _load_pipeline(args.model_id, allow_download=args.allow_download)
    demo = _build_demo(pipeline)
    demo.queue().launch(server_name=args.host, server_port=args.port, share=args.share)
    return 0


if __name__ == "__main__":
    sys.exit(main())
