#!/usr/bin/env python3
"""Run Helios generation with the installed diffusers API.

This helper keeps the common Helios generation path self-contained:
text-to-video, image-to-video, and video-to-video generation with the public
Helios diffusers classes.
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import torch
import torch.distributed as dist
from diffusers import AutoencoderKLWan, ContextParallelConfig, HeliosDMDScheduler, HeliosPyramidPipeline, HeliosScheduler
from diffusers.utils import export_to_video, load_image, load_video


DEFAULT_PROMPT = (
    "A vibrant tropical fish swimming gracefully among colorful coral reefs in a clear, turquoise ocean. "
    "The fish has bright blue and yellow scales with a small, distinctive orange spot on its side, its fins "
    "moving fluidly. The coral reefs are alive with a variety of marine life, including small schools of "
    "colorful fish and sea turtles gliding by."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Helios video with the diffusers API")
    parser.add_argument("--model-id", default="BestWishYsh/Helios-Distilled", help="Helios checkpoint ID")
    parser.add_argument("--mode", choices=["t2v", "i2v", "v2v"], default="t2v", help="Generation mode")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="Text prompt")
    parser.add_argument("--negative-prompt", default=None, help="Optional negative prompt")
    parser.add_argument("--image-path", default=None, help="Image input for i2v")
    parser.add_argument("--video-path", default=None, help="Video input for v2v")
    parser.add_argument("--output", default="outputs/helios.mp4", help="Output mp4 path or directory")
    parser.add_argument("--height", type=int, default=384, help="Output height")
    parser.add_argument("--width", type=int, default=640, help="Output width")
    parser.add_argument("--num-frames", type=int, default=132, help="Number of generated frames")
    parser.add_argument("--guidance-scale", type=float, default=5.0, help="Guidance scale")
    parser.add_argument(
        "--pyramid-steps",
        type=int,
        nargs="+",
        default=[2, 2, 2],
        help="Per-stage step counts for the pyramid pipeline",
    )
    parser.add_argument(
        "--history-sizes",
        type=int,
        nargs="+",
        default=[16, 2, 1],
        help="History sizes for the chunked generation path",
    )
    parser.add_argument("--num-latent-frames-per-chunk", type=int, default=9, help="Latent frames per chunk")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--distilled", action="store_true", help="Use the distilled scheduler path")
    parser.add_argument("--low-vram", action="store_true", help="Enable group offload")
    parser.add_argument("--offload-type", choices=["leaf_level", "block_level"], default="leaf_level")
    parser.add_argument("--skip-first-chunk", action="store_true", help="Skip the first chunk")
    parser.add_argument("--amplify-first-chunk", action="store_true", help="Boost the first chunk")
    parser.add_argument("--use-zero-init", dest="use_zero_init", action="store_true", help="Enable zero init")
    parser.add_argument("--no-use-zero-init", dest="use_zero_init", action="store_false", help="Disable zero init")
    parser.set_defaults(use_zero_init=True)
    parser.add_argument("--zero-steps", type=int, default=1, help="Zero-init steps")
    parser.add_argument("--parallelism", action="store_true", help="Enable context parallelism if launched with torchrun")
    parser.add_argument(
        "--cp-backend",
        choices=["ring", "ulysses", "unified", "ulysses_anything"],
        default="ulysses",
        help="Context parallel backend",
    )
    parser.add_argument(
        "--image-noise-sigma-min",
        type=float,
        default=0.111,
        help="Lower image-noise sigma bound",
    )
    parser.add_argument(
        "--image-noise-sigma-max",
        type=float,
        default=0.135,
        help="Upper image-noise sigma bound",
    )
    parser.add_argument(
        "--video-noise-sigma-min",
        type=float,
        default=0.111,
        help="Lower video-noise sigma bound",
    )
    parser.add_argument(
        "--video-noise-sigma-max",
        type=float,
        default=0.135,
        help="Upper video-noise sigma bound",
    )
    return parser.parse_args()


def resolve_output_path(output: str, mode: str) -> Path:
    path = Path(output)
    if path.suffix.lower() == ".mp4":
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    path.mkdir(parents=True, exist_ok=True)
    return path / f"helios_{mode}_{int(time.time())}.mp4"


def pick_attention_backend(transformer) -> None:
    if not hasattr(transformer, "set_attention_backend") or not torch.cuda.is_available():
        return

    try:
        major, _minor = torch.cuda.get_device_capability()
    except Exception:
        return

    if major >= 9:
        try:
            transformer.set_attention_backend("_flash_3_hub")
            return
        except Exception:
            transformer.set_attention_backend("flash_hub")
            return

    transformer.set_attention_backend("flash_hub")


def build_pipe(model_id: str, distilled: bool, device: torch.device):
    if not torch.cuda.is_available():
        raise RuntimeError("Helios generation needs a CUDA-capable GPU backend.")

    scheduler_cls = HeliosDMDScheduler if distilled else HeliosScheduler
    vae = AutoencoderKLWan.from_pretrained(model_id, subfolder="vae", torch_dtype=torch.float32)
    scheduler = scheduler_cls.from_pretrained(model_id, subfolder="scheduler")
    pipe = HeliosPyramidPipeline.from_pretrained(
        model_id,
        vae=vae,
        scheduler=scheduler,
        torch_dtype=torch.bfloat16,
        is_distilled=distilled,
    )
    pipe.to(device)
    pick_attention_backend(pipe.transformer)
    return pipe


def maybe_enable_low_vram(pipe, offload_type: str, device: torch.device):
    if not hasattr(pipe, "enable_group_offload"):
        return

    pipe.enable_group_offload(
        onload_device=device,
        offload_device=torch.device("cpu"),
        offload_type=offload_type,
        use_stream=True,
        record_stream=True,
    )


def main() -> int:
    args = parse_args()
    if not torch.cuda.is_available():
        raise SystemExit("CUDA is required for Helios generation in this helper.")

    if args.mode == "i2v" and not args.image_path:
        raise SystemExit("--image-path is required for image-to-video mode.")
    if args.mode == "v2v" and not args.video_path:
        raise SystemExit("--video-path is required for video-to-video mode.")

    rank = 0
    world_size = 1
    device = torch.device("cuda")
    if dist.is_available() and "RANK" in os.environ:
        backend = "cpu:gloo,cuda:nccl" if args.cp_backend == "ulysses_anything" else "nccl"
        dist.init_process_group(backend=backend)
        rank = dist.get_rank()
        world_size = dist.get_world_size()
        device = torch.device("cuda", rank % torch.cuda.device_count())
        torch.cuda.set_device(device)

    if world_size > 1 and args.low_vram:
        raise SystemExit("--low-vram is only supported for single-GPU runs; disable it for context parallelism.")

    pipe = build_pipe(args.model_id, distilled=args.distilled, device=device)

    if args.low_vram:
        maybe_enable_low_vram(pipe, args.offload_type, device=device)

    if args.parallelism and world_size > 1 and hasattr(pipe.transformer, "enable_parallelism"):
        if args.cp_backend == "ring":
            cp_config = ContextParallelConfig(ring_degree=world_size)
        elif args.cp_backend == "unified":
            cp_config = ContextParallelConfig(ring_degree=world_size // 2, ulysses_degree=world_size // 2)
        elif args.cp_backend == "ulysses":
            cp_config = ContextParallelConfig(ulysses_degree=world_size)
        else:
            cp_config = ContextParallelConfig(ulysses_degree=world_size, ulysses_anything=True)
        pipe.transformer.enable_parallelism(config=cp_config)

    image = None
    video = None
    if args.mode == "i2v":
        image = load_image(args.image_path).resize((args.width, args.height))
    elif args.mode == "v2v":
        video = load_video(args.video_path)

    generator = torch.Generator(device=device).manual_seed(args.seed)
    with torch.no_grad():
        output = pipe(
            prompt=args.prompt,
            negative_prompt=args.negative_prompt,
            height=args.height,
            width=args.width,
            num_frames=args.num_frames,
            guidance_scale=args.guidance_scale,
            generator=generator,
            output_type="np",
            pyramid_num_inference_steps_list=args.pyramid_steps,
            history_sizes=args.history_sizes,
            num_latent_frames_per_chunk=args.num_latent_frames_per_chunk,
            keep_first_frame=True,
            is_skip_first_chunk=args.skip_first_chunk,
            use_zero_init=args.use_zero_init,
            zero_steps=args.zero_steps,
            is_amplify_first_chunk=args.amplify_first_chunk,
            image=image,
            video=video,
            image_noise_sigma_min=args.image_noise_sigma_min,
            image_noise_sigma_max=args.image_noise_sigma_max,
            video_noise_sigma_min=args.video_noise_sigma_min,
            video_noise_sigma_max=args.video_noise_sigma_max,
        ).frames[0]

    output_path = resolve_output_path(args.output, args.mode)
    export_to_video(output, str(output_path), fps=24)
    print(f"Saved {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
