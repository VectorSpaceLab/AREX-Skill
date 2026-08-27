#!/usr/bin/env python3
"""DreamOmni2 Gradio editing demo."""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

import gradio as gr

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from dreamomni2_common import DEFAULT_BASE_MODEL, run_dreamomni2_workflow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch the DreamOmni2 editing Gradio demo.")
    parser.add_argument(
        "--vlm-path",
        default="models/vlm-model",
        help="Path to the Qwen2.5-VL checkpoint directory or hub id.",
    )
    parser.add_argument(
        "--edit-lora-path",
        default="models/edit_lora",
        help="Path to the editing LoRA directory or hub id.",
    )
    parser.add_argument(
        "--base-model-path",
        default=DEFAULT_BASE_MODEL,
        help="DreamOmni2 base diffusion model directory or hub id.",
    )
    parser.add_argument("--server_name", default="0.0.0.0", help="Host interface for Gradio.")
    parser.add_argument("--server_port", type=int, default=7860, help="Port for Gradio.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    def process_request(image_file_1, image_file_2, instruction):
        if not image_file_1 or not image_file_2:
            raise gr.Error("Please upload both images.")
        if not instruction:
            raise gr.Error("Please provide an instruction.")
        output_path = Path("/tmp") / f"dreamomni2-edit-{uuid.uuid4().hex}.png"
        run_dreamomni2_workflow(
            mode="edit",
            image_paths=[image_file_1, image_file_2],
            instruction=instruction,
            output_path=output_path,
            vlm_path=args.vlm_path,
            adapter_path=args.edit_lora_path,
            base_model_path=args.base_model_path,
        )
        return str(output_path)

    css = """
    .text-center { text-align: center; }
    .result-img img {
        max-height: 60vh !important;
        min-height: 30vh !important;
        width: auto !important;
        object-fit: contain;
    }
    .input-img img {
        max-height: 30vh !important;
        width: auto !important;
        object-fit: contain;
    }
    """

    with gr.Blocks(theme=gr.themes.Soft(), title="DreamOmni2 Editing", css=css) as demo:
        gr.Markdown(
            "# DreamOmni2 editing demo\n\nUpload the source image first, the reference image second, and describe the edit you want.",
            elem_classes="text-center",
        )
        with gr.Row():
            with gr.Column(scale=2):
                image_uploader_1 = gr.Image(label="Source image", type="filepath", interactive=True, elem_classes="input-img")
                image_uploader_2 = gr.Image(label="Reference image", type="filepath", interactive=True, elem_classes="input-img")
                instruction_text = gr.Textbox(
                    label="Instruction",
                    lines=2,
                    placeholder="Describe the edit you want DreamOmni2 to make.",
                )
                run_button = gr.Button("Run", variant="primary")
            with gr.Column(scale=2):
                output_image = gr.Image(label="Result", type="filepath", elem_classes="result-img")

        run_button.click(fn=process_request, inputs=[image_uploader_1, image_uploader_2, instruction_text], outputs=output_image)

    demo.launch(server_name=args.server_name, server_port=args.server_port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
