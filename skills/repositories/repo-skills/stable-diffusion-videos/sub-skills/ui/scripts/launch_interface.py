#!/usr/bin/env python3
"""Configurable launcher for stable_diffusion_videos.Interface.

The default is a dry run. Pass --run when you are ready to load the model and
start Gradio.
"""

from __future__ import annotations

import argparse
import json
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-id", default="runwayml/stable-diffusion-v1-5")
    parser.add_argument("--vae-id", default="stabilityai/sd-vae-ft-mse", help="Optional VAE model id; pass empty string to skip.")
    parser.add_argument("--scheduler", choices=["default", "lms"], default="lms")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--dtype", choices=["float16", "float32", "bfloat16"], default="float16")
    parser.add_argument("--safety-checker-none", action="store_true")
    parser.add_argument("--xformers-auto", action="store_true", help="Enable xformers if diffusers reports it is available.")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--share", action="store_true")
    parser.add_argument("--server-name", help="Optional Gradio server_name.")
    parser.add_argument("--server-port", type=int, help="Optional Gradio server_port.")
    parser.add_argument("--dry-run", action="store_true", help="Print config and exit. This is also the default without --run.")
    parser.add_argument("--run", action="store_true", help="Load the model and launch Gradio.")
    return parser


def dry_payload(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "model_id": args.model_id,
        "vae_id": args.vae_id or None,
        "scheduler": args.scheduler,
        "device": args.device,
        "dtype": args.dtype,
        "safety_checker_none": args.safety_checker_none,
        "xformers_auto": args.xformers_auto,
        "launch_kwargs": {
            "debug": args.debug,
            "share": args.share,
            "server_name": args.server_name,
            "server_port": args.server_port,
        },
    }


def main() -> int:
    args = build_parser().parse_args()
    payload = dry_payload(args)
    if args.dry_run or not args.run:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    import torch
    from diffusers.models import AutoencoderKL
    from diffusers.schedulers import LMSDiscreteScheduler
    from stable_diffusion_videos import Interface, StableDiffusionWalkPipeline

    dtype = getattr(torch, args.dtype)
    from_pretrained_kwargs: dict[str, Any] = {"torch_dtype": dtype}
    if args.safety_checker_none:
        from_pretrained_kwargs["safety_checker"] = None
    if args.vae_id:
        from_pretrained_kwargs["vae"] = AutoencoderKL.from_pretrained(args.vae_id, torch_dtype=dtype).to(args.device)
    if args.scheduler == "lms":
        from_pretrained_kwargs["scheduler"] = LMSDiscreteScheduler(
            beta_start=0.00085,
            beta_end=0.012,
            beta_schedule="scaled_linear",
        )

    pipe = StableDiffusionWalkPipeline.from_pretrained(args.model_id, **from_pretrained_kwargs).to(args.device)

    if args.xformers_auto:
        try:
            from diffusers.utils.import_utils import is_xformers_available

            if is_xformers_available():
                pipe.enable_xformers_memory_efficient_attention()
        except Exception as exc:
            print(f"xformers auto-enable skipped: {type(exc).__name__}: {exc}")

    interface = Interface(pipe)
    launch_kwargs: dict[str, Any] = {"debug": args.debug, "share": args.share}
    if args.server_name:
        launch_kwargs["server_name"] = args.server_name
    if args.server_port is not None:
        launch_kwargs["server_port"] = args.server_port
    interface.launch(**launch_kwargs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
