#!/usr/bin/env python3
"""Bundled HunyuanVideo Gradio server runner.

This self-contained runner mirrors the repository web demo while importing an
installed/importable `hyvideo` package, or a local source tree when --repo-root
is supplied. It starts a real Gradio service and loads model weights, so run it
only after checkpoint/CUDA preflights and service exposure are approved.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path


def build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch bundled HunyuanVideo Gradio demo.")
    parser.add_argument("--repo-root", default=None, help="Optional HunyuanVideo source root containing hyvideo/. Omit when hyvideo is importable.")
    parser.add_argument("--model-base", default="ckpts")
    parser.add_argument("--save-path", default="./results")
    parser.add_argument("--flow-reverse", action="store_true")
    # Shared HunyuanVideo defaults consumed by model construction.
    parser.add_argument("--model", default="HYVideo-T/2-cfgdistill", choices=["HYVideo-T/2", "HYVideo-T/2-cfgdistill"])
    parser.add_argument("--latent-channels", type=int, default=16)
    parser.add_argument("--precision", default="bf16")
    parser.add_argument("--vae", default="884-16c-hy")
    parser.add_argument("--vae-precision", default="fp16")
    parser.add_argument("--vae-tiling", action="store_true", default=True)
    parser.add_argument("--text-encoder", default="llm")
    parser.add_argument("--text-encoder-precision", default="fp16")
    parser.add_argument("--text-states-dim", type=int, default=4096)
    parser.add_argument("--text-len", type=int, default=256)
    parser.add_argument("--tokenizer", default="llm")
    parser.add_argument("--prompt-template", default="dit-llm-encode")
    parser.add_argument("--prompt-template-video", default="dit-llm-encode-video")
    parser.add_argument("--hidden-state-skip-layer", type=int, default=2)
    parser.add_argument("--apply-final-norm", action="store_true")
    parser.add_argument("--text-encoder-2", default="clipL")
    parser.add_argument("--text-encoder-precision-2", default="fp16")
    parser.add_argument("--text-states-dim-2", type=int, default=768)
    parser.add_argument("--tokenizer-2", default="clipL")
    parser.add_argument("--text-len-2", type=int, default=77)
    parser.add_argument("--denoise-type", default="flow")
    parser.add_argument("--flow-shift", type=float, default=7.0)
    parser.add_argument("--flow-solver", default="euler")
    parser.add_argument("--model-resolution", default="540p", choices=["540p", "720p"])
    parser.add_argument("--dit-weight", default="ckpts/hunyuan-video-t2v-720p/transformers/mp_rank_00_model_states.pt")
    parser.add_argument("--load-key", default="module")
    parser.add_argument("--use-cpu-offload", action="store_true")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--infer-steps", type=int, default=50)
    parser.add_argument("--disable-autocast", action="store_true")
    parser.add_argument("--save-path-suffix", default="")
    parser.add_argument("--name-suffix", default="")
    parser.add_argument("--num-videos", type=int, default=1)
    parser.add_argument("--video-size", type=int, nargs="+", default=(720, 1280))
    parser.add_argument("--video-length", type=int, default=129)
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--seed-type", default="auto")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--neg-prompt", default=None)
    parser.add_argument("--cfg-scale", type=float, default=1.0)
    parser.add_argument("--embedded-cfg-scale", type=float, default=6.0)
    parser.add_argument("--use-fp8", action="store_true")
    parser.add_argument("--reproduce", action="store_true")
    parser.add_argument("--ulysses-degree", type=int, default=1)
    parser.add_argument("--ring-degree", type=int, default=1)
    parser.add_argument("--rope-theta", type=int, default=256)
    parser.add_argument("--use-linear-quadratic-schedule", action="store_true")
    parser.add_argument("--linear-schedule-end", type=int, default=25)
    return parser.parse_args()


def main() -> int:
    args = build_args()
    if args.repo_root:
        repo_root = Path(args.repo_root).expanduser().resolve()
        if not (repo_root / "hyvideo").exists():
            raise SystemExit(f"--repo-root does not contain a hyvideo package: {repo_root}")
        sys.path.insert(0, str(repo_root))

    try:
        import gradio as gr
        from loguru import logger
        from hyvideo.inference import HunyuanVideoSampler
        from hyvideo.utils.file_utils import save_videos_grid
    except ImportError as exc:
        raise SystemExit("Could not import HunyuanVideo/Gradio. Install dependencies and hyvideo in the active environment or pass --repo-root to a source tree containing hyvideo/.") from exc

    model_root = Path(args.model_base)
    if not model_root.exists():
        raise SystemExit(f"`models_root` not exists: {model_root}")

    sampler = HunyuanVideoSampler.from_pretrained(model_root, args=args)

    def generate_video(prompt, resolution, video_length, seed, num_inference_steps, guidance_scale, flow_shift, embedded_guidance_scale):
        seed = None if seed == -1 else seed
        width_s, height_s = resolution.split("x")
        width, height = int(width_s), int(height_s)
        outputs = sampler.predict(
            prompt=prompt,
            height=height,
            width=width,
            video_length=int(video_length),
            seed=seed,
            negative_prompt="",
            infer_steps=int(num_inference_steps),
            guidance_scale=float(guidance_scale),
            num_videos_per_prompt=1,
            flow_shift=float(flow_shift),
            batch_size=1,
            embedded_guidance_scale=float(embedded_guidance_scale),
        )
        sample = outputs["samples"][0].unsqueeze(0)
        out_dir = Path.cwd() / "gradio_outputs"
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d-%H:%M:%S")
        out_path = out_dir / f"{stamp}_seed{outputs['seeds'][0]}_{outputs['prompts'][0][:100].replace('/', '')}.mp4"
        save_videos_grid(sample, str(out_path), fps=24)
        logger.info(f"Sample saved to: {out_path}")
        return str(out_path)

    with gr.Blocks() as demo:
        gr.Markdown("# Hunyuan Video Generation")
        with gr.Row():
            with gr.Column():
                prompt = gr.Textbox(label="Prompt", value="A cat walks on the grass, realistic style.")
                with gr.Row():
                    resolution = gr.Dropdown(
                        choices=[
                            ("1280x720 (16:9, 720p)", "1280x720"),
                            ("720x1280 (9:16, 720p)", "720x1280"),
                            ("1104x832 (4:3, 720p)", "1104x832"),
                            ("832x1104 (3:4, 720p)", "832x1104"),
                            ("960x960 (1:1, 720p)", "960x960"),
                            ("960x544 (16:9, 540p)", "960x544"),
                            ("544x960 (9:16, 540p)", "544x960"),
                            ("832x624 (4:3, 540p)", "832x624"),
                            ("624x832 (3:4, 540p)", "624x832"),
                            ("720x720 (1:1, 540p)", "720x720"),
                        ],
                        value="1280x720",
                        label="Resolution",
                    )
                    video_length = gr.Dropdown(label="Video Length", choices=[("2s(65f)", 65), ("5s(129f)", 129)], value=129)
                num_inference_steps = gr.Slider(1, 100, value=50, step=1, label="Number of Inference Steps")
                show_advanced = gr.Checkbox(label="Show Advanced Options", value=False)
                with gr.Row(visible=False) as advanced_row:
                    with gr.Column():
                        seed = gr.Number(value=-1, label="Seed (-1 for random)")
                        guidance_scale = gr.Slider(1.0, 20.0, value=1.0, step=0.5, label="Guidance Scale")
                        flow_shift = gr.Slider(0.0, 10.0, value=7.0, step=0.1, label="Flow Shift")
                        embedded_guidance_scale = gr.Slider(1.0, 20.0, value=6.0, step=0.5, label="Embedded Guidance Scale")
                show_advanced.change(fn=lambda x: gr.Row(visible=x), inputs=[show_advanced], outputs=[advanced_row])
                generate_btn = gr.Button("Generate")
            with gr.Column():
                output = gr.Video(label="Generated Video")
        generate_btn.click(fn=generate_video, inputs=[prompt, resolution, video_length, seed, num_inference_steps, guidance_scale, flow_shift, embedded_guidance_scale], outputs=output)

    os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")
    server_name = os.getenv("SERVER_NAME", "0.0.0.0")
    server_port = int(os.getenv("SERVER_PORT", "8081"))
    demo.launch(server_name=server_name, server_port=server_port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
