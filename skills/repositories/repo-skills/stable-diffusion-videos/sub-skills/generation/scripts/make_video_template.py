#!/usr/bin/env python3
"""Build or run a stable-diffusion-videos walk call.

Default behavior is a dry run that validates prompts/seeds and prints the walk
configuration. Pass --run only when you are ready for model downloads and GPU
execution.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", action="append", required=True, help="Prompt text. Repeat once per walk point.")
    parser.add_argument("--seed", action="append", type=int, required=True, help="Seed. Repeat once per prompt.")
    parser.add_argument(
        "--num-interpolation-steps",
        action="append",
        type=int,
        help="Interpolation steps. Omit for 5, pass once to reuse, or repeat once per prompt gap.",
    )
    parser.add_argument("--audio-filepath", type=Path, help="Optional audio file for music-paced interpolation.")
    parser.add_argument("--audio-offset", action="append", type=float, help="Audio boundary in seconds. Repeat once per prompt.")
    parser.add_argument("--fps", type=int, default=30, help="Output video FPS.")
    parser.add_argument("--output-dir", default="dreams", help="Output directory.")
    parser.add_argument("--name", help="Run name under output-dir.")
    parser.add_argument("--height", type=int, default=512)
    parser.add_argument("--width", type=int, default=512)
    parser.add_argument("--num-inference-steps", type=int, default=50)
    parser.add_argument("--guidance-scale", type=float, default=7.5)
    parser.add_argument("--eta", type=float, default=0.0)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--upsample", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--margin", type=float, default=1.0)
    parser.add_argument("--smooth", type=float, default=0.0)
    parser.add_argument("--negative-prompt")
    parser.add_argument("--no-video", action="store_true", help="Generate frames but skip MP4 encoding.")
    parser.add_argument("--model-id", default="CompVis/stable-diffusion-v1-4")
    parser.add_argument("--revision", help="Optional model revision, for example fp16.")
    parser.add_argument("--device", default="cuda", help="Device passed to pipeline.to(...).")
    parser.add_argument("--dtype", choices=["float16", "float32", "bfloat16"], default="float16")
    parser.add_argument("--tiled", action="store_true", help="Use the pipeline's tiled from_pretrained option.")
    parser.add_argument("--safety-checker-none", action="store_true", help="Pass safety_checker=None to from_pretrained.")
    parser.add_argument("--run", action="store_true", help="Actually load the model and run the walk.")
    parser.add_argument("--json", action="store_true", help="Emit dry-run config as JSON.")
    return parser


def derive_steps(args: argparse.Namespace) -> int | list[int]:
    prompts = args.prompt
    gaps = len(prompts) - 1
    if gaps <= 0:
        raise SystemExit("provide at least two --prompt values")

    if args.audio_offset:
        if len(args.audio_offset) != len(prompts):
            raise SystemExit("--audio-offset must be repeated once per prompt")
        if args.audio_filepath is None:
            raise SystemExit("--audio-filepath is required when --audio-offset is used")
        return [int(round((b - a) * args.fps)) for a, b in zip(args.audio_offset, args.audio_offset[1:])]

    if not args.num_interpolation_steps:
        return 5
    if len(args.num_interpolation_steps) == 1:
        return args.num_interpolation_steps[0]
    if len(args.num_interpolation_steps) == gaps:
        return args.num_interpolation_steps
    raise SystemExit("--num-interpolation-steps must be omitted, passed once, or repeated once per prompt gap")


def build_walk_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    if len(args.seed) != len(args.prompt):
        raise SystemExit("--seed must be repeated once per --prompt")
    if args.height % 8 != 0 or args.width % 8 != 0:
        raise SystemExit("--height and --width must be divisible by 8")
    if args.fps <= 0:
        raise SystemExit("--fps must be positive")

    steps = derive_steps(args)
    kwargs: dict[str, Any] = {
        "prompts": args.prompt,
        "seeds": args.seed,
        "num_interpolation_steps": steps,
        "output_dir": args.output_dir,
        "name": args.name,
        "fps": args.fps,
        "num_inference_steps": args.num_inference_steps,
        "guidance_scale": args.guidance_scale,
        "eta": args.eta,
        "height": args.height,
        "width": args.width,
        "upsample": args.upsample,
        "batch_size": args.batch_size,
        "resume": args.resume,
        "audio_filepath": str(args.audio_filepath) if args.audio_filepath else None,
        "audio_start_sec": args.audio_offset[0] if args.audio_offset else None,
        "margin": args.margin,
        "smooth": args.smooth,
        "negative_prompt": args.negative_prompt,
        "make_video": not args.no_video,
    }
    return kwargs


def main() -> int:
    args = build_parser().parse_args()
    walk_kwargs = build_walk_kwargs(args)

    dry_payload = {
        "model_id": args.model_id,
        "revision": args.revision,
        "device": args.device,
        "dtype": args.dtype,
        "tiled": args.tiled,
        "safety_checker_none": args.safety_checker_none,
        "walk_kwargs": walk_kwargs,
    }

    if args.json or not args.run:
        print(json.dumps(dry_payload, indent=2, sort_keys=True))

    if not args.run:
        return 0

    if args.audio_filepath and not args.audio_filepath.exists():
        raise SystemExit(f"audio file not found: {args.audio_filepath}")

    import torch
    from stable_diffusion_videos import StableDiffusionWalkPipeline

    dtype = getattr(torch, args.dtype)
    from_pretrained_kwargs: dict[str, Any] = {"torch_dtype": dtype, "tiled": args.tiled}
    if args.revision:
        from_pretrained_kwargs["revision"] = args.revision
    if args.safety_checker_none:
        from_pretrained_kwargs["safety_checker"] = None

    pipe = StableDiffusionWalkPipeline.from_pretrained(args.model_id, **from_pretrained_kwargs).to(args.device)
    video_path = pipe.walk(**walk_kwargs)
    print(video_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
