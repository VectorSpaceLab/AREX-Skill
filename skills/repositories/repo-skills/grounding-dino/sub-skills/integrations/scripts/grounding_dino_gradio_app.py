#!/usr/bin/env python3
"""Safe GroundingDINO Gradio launcher.

This wrapper preserves the useful web-demo pattern while avoiding source-demo
side effects. It never runs setup.py or pip install. Optional UI/download
packages are imported only after argparse succeeds, so --help remains safe in a
minimal environment.
"""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import sys
from pathlib import Path
from typing import List, Optional, Tuple


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Launch a safe GroundingDINO Gradio demo with explicit config and checkpoint paths."
    )
    parser.add_argument("--config", required=True, help="Path to a GroundingDINO model config .py file.")
    parser.add_argument("--checkpoint", required=True, help="Local checkpoint path to load, or target path for HF download.")
    parser.add_argument("--hf-repo-id", help="Optional Hugging Face repo id. No download occurs unless paired with --hf-filename.")
    parser.add_argument("--hf-filename", help="Optional Hugging Face checkpoint filename. Requires --hf-repo-id.")
    parser.add_argument("--device", default="cpu", help="Torch device for model inference, for example cpu, cuda, or cuda:0.")
    parser.add_argument("--server-name", default="127.0.0.1", help="Gradio bind host. Use 0.0.0.0 only on trusted networks.")
    parser.add_argument("--server-port", type=int, default=7579, help="Gradio server port.")
    parser.add_argument("--share", action="store_true", help="Request a public Gradio share URL.")
    parser.add_argument("--box-threshold", type=float, default=0.25, help="Initial UI box threshold slider value.")
    parser.add_argument("--text-threshold", type=float, default=0.25, help="Initial UI text threshold slider value.")
    return parser


def require_module(module_name: str, install_hint: str) -> None:
    if importlib.util.find_spec(module_name) is None:
        raise SystemExit(
            f"Missing optional dependency '{module_name}'. Install it outside this script, for example: {install_hint}"
        )


def validate_args(args: argparse.Namespace) -> Tuple[Path, Path]:
    config_path = Path(args.config).expanduser()
    checkpoint_path = Path(args.checkpoint).expanduser()

    if not config_path.is_file():
        raise SystemExit(f"Config file does not exist: {config_path}")

    has_hf_repo = bool(args.hf_repo_id)
    has_hf_filename = bool(args.hf_filename)
    if has_hf_repo != has_hf_filename:
        raise SystemExit("Provide both --hf-repo-id and --hf-filename, or neither. No partial HF download is attempted.")

    if not (0.0 <= args.box_threshold <= 1.0):
        raise SystemExit("--box-threshold must be between 0 and 1.")
    if not (0.0 <= args.text_threshold <= 1.0):
        raise SystemExit("--text-threshold must be between 0 and 1.")
    if not (1 <= args.server_port <= 65535):
        raise SystemExit("--server-port must be between 1 and 65535.")

    return config_path, checkpoint_path


def maybe_download_checkpoint(args: argparse.Namespace, checkpoint_path: Path) -> Path:
    if not args.hf_repo_id and not args.hf_filename:
        if not checkpoint_path.is_file():
            raise SystemExit(
                f"Checkpoint file does not exist: {checkpoint_path}. Provide a local file or pass both --hf-repo-id and --hf-filename."
            )
        return checkpoint_path

    require_module("huggingface_hub", "python -m pip install huggingface_hub")
    from huggingface_hub import hf_hub_download

    try:
        cached_path = Path(hf_hub_download(repo_id=args.hf_repo_id, filename=args.hf_filename))
    except Exception as exc:
        raise SystemExit(f"Hugging Face download failed for {args.hf_repo_id}/{args.hf_filename}: {exc}") from exc

    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    if cached_path.resolve() != checkpoint_path.resolve():
        shutil.copy2(cached_path, checkpoint_path)
    return checkpoint_path


def load_pil_image_for_grounding(pil_image):
    import groundingdino.datasets.transforms as transforms

    transform = transforms.Compose(
        [
            transforms.RandomResize([800], max_size=1333),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    rgb_image = pil_image.convert("RGB")
    image_tensor, _ = transform(rgb_image, None)
    return rgb_image, image_tensor


def make_app(args: argparse.Namespace, config_path: Path, checkpoint_path: Path):
    require_module("gradio", "python -m pip install gradio")

    import cv2
    import gradio as gr
    import numpy as np
    from PIL import Image

    from groundingdino.util.inference import annotate, load_model, predict

    model = load_model(str(config_path), str(checkpoint_path), device=args.device)

    def run_grounding(input_image: Image.Image, prompt: str, box_threshold: float, text_threshold: float) -> Image.Image:
        if input_image is None:
            raise gr.Error("Upload an image before running GroundingDINO.")
        if not prompt or not prompt.strip():
            raise gr.Error("Enter a detection prompt such as 'cat . dog .'.")

        rgb_image, image_tensor = load_pil_image_for_grounding(input_image)
        boxes, logits, phrases = predict(
            model=model,
            image=image_tensor,
            caption=prompt,
            box_threshold=box_threshold,
            text_threshold=text_threshold,
            device=args.device,
        )
        annotated_bgr = annotate(
            image_source=np.asarray(rgb_image),
            boxes=boxes,
            logits=logits,
            phrases=phrases,
        )
        annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
        return Image.fromarray(annotated_rgb)

    with gr.Blocks(title="GroundingDINO Demo") as app:
        gr.Markdown("# GroundingDINO Web Demo")
        gr.Markdown(
            "Upload an RGB image, enter an open-vocabulary prompt such as `cat . dog .`, "
            "and tune thresholds. This safe wrapper does not install packages or build the repo."
        )
        with gr.Row():
            with gr.Column():
                input_image = gr.Image(type="pil", label="Image")
                prompt = gr.Textbox(label="Detection Prompt", placeholder="cat . dog .")
                run_button = gr.Button("Run GroundingDINO", variant="primary")
                with gr.Accordion("Advanced thresholds", open=False):
                    box_threshold = gr.Slider(0.0, 1.0, value=args.box_threshold, step=0.001, label="Box Threshold")
                    text_threshold = gr.Slider(0.0, 1.0, value=args.text_threshold, step=0.001, label="Text Threshold")
            with gr.Column():
                output_image = gr.Image(type="pil", label="Annotated Result")

        run_button.click(
            fn=run_grounding,
            inputs=[input_image, prompt, box_threshold, text_threshold],
            outputs=output_image,
        )

    return app


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config_path, checkpoint_path = validate_args(args)
    checkpoint_path = maybe_download_checkpoint(args, checkpoint_path)
    app = make_app(args, config_path, checkpoint_path)
    app.queue().launch(server_name=args.server_name, server_port=args.server_port, share=args.share)
    return 0


if __name__ == "__main__":
    sys.exit(main())
