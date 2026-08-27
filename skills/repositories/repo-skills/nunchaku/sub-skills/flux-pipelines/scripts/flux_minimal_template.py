#!/usr/bin/env python3
"""Minimal parameterized Nunchaku FLUX generation template.

This script intentionally does not hard-code credentials, private caches, or local
model paths. It produces one image when the selected base model and Nunchaku
transformer asset are accessible to the current Python environment.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate one image with a Nunchaku FLUX transformer in Diffusers.")
    parser.add_argument(
        "--transformer",
        required=True,
        help="Nunchaku quantized transformer asset: HF model-file path or local .safetensors/.sft path.",
    )
    parser.add_argument(
        "--base-model",
        default="black-forest-labs/FLUX.1-dev",
        help="Diffusers FLUX base model id or local model path.",
    )
    parser.add_argument(
        "--prompt",
        default="A cat holding a sign that says hello world",
        help="Prompt for the single generated image.",
    )
    parser.add_argument("--output", default="flux-output.png", help="Output image path.")
    parser.add_argument(
        "--dtype",
        default="auto",
        choices=("auto", "bf16", "bfloat16", "fp16", "float16"),
        help="Pipeline and transformer dtype. Use fp16/float16 for Turing GPUs.",
    )
    parser.add_argument("--device", default="cuda", help="Torch device for non-offloaded generation, e.g. cuda or cuda:1.")
    parser.add_argument(
        "--offload",
        action="store_true",
        help="Enable low-memory offload. For the legacy Nunchaku FLUX class this also passes offload=True while loading.",
    )
    parser.add_argument(
        "--turing-fp16-attn",
        action="store_true",
        help="Use the documented Turing path: fp16 dtype and nunchaku-fp16 attention when supported.",
    )
    parser.add_argument(
        "--loader",
        choices=("legacy", "v2"),
        default="legacy",
        help="Use NunchakuFluxTransformer2dModel (legacy/current examples) or NunchakuFluxTransformer2DModelV2.",
    )
    parser.add_argument("--steps", type=int, default=None, help="Number of inference steps. Defaults to 4 for schnell, else 20.")
    parser.add_argument("--guidance-scale", type=float, default=None, help="Guidance scale. Defaults to 0 for schnell, else 3.5.")
    parser.add_argument("--height", type=int, default=None, help="Optional output height.")
    parser.add_argument("--width", type=int, default=None, help="Optional output width.")
    parser.add_argument("--seed", type=int, default=None, help="Optional torch random seed.")
    return parser.parse_args()


def resolve_dtype(dtype_name: str, turing_fp16_attn: bool):
    import torch

    if dtype_name in {"fp16", "float16"} or turing_fp16_attn:
        return torch.float16
    if dtype_name in {"bf16", "bfloat16", "auto"}:
        return torch.bfloat16
    raise ValueError(f"Unsupported dtype: {dtype_name}")


def cuda_index(device: str) -> int | None:
    if not device.startswith("cuda"):
        return None
    parts = device.split(":", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return int(parts[1])
    return None


def enable_sequential_offload(pipe, device: str) -> None:
    idx = cuda_index(device)
    if idx is None:
        pipe.enable_sequential_cpu_offload()
    else:
        pipe.enable_sequential_cpu_offload(gpu_id=idx)


def main() -> int:
    args = parse_args()

    import torch
    from diffusers import FluxPipeline
    from nunchaku import NunchakuFluxTransformer2DModelV2, NunchakuFluxTransformer2dModel

    dtype = resolve_dtype(args.dtype, args.turing_fp16_attn)

    if args.loader == "legacy":
        load_kwargs = {"torch_dtype": dtype, "device": args.device, "offload": args.offload}
        transformer = NunchakuFluxTransformer2dModel.from_pretrained(args.transformer, **load_kwargs)
        if args.turing_fp16_attn:
            transformer.set_attention_impl("nunchaku-fp16")
    else:
        if args.offload:
            print(
                "warning: NunchakuFluxTransformer2DModelV2 source does not support from_pretrained(offload=True); "
                "loading on CPU and enabling Diffusers sequential CPU offload.",
                file=sys.stderr,
            )
        if args.turing_fp16_attn:
            print(
                "warning: --turing-fp16-attn is documented for NunchakuFluxTransformer2dModel; "
                "V2 will use fp16 dtype but no attention switch is applied.",
                file=sys.stderr,
            )
        load_device = "cpu" if args.offload else args.device
        transformer = NunchakuFluxTransformer2DModelV2.from_pretrained(
            args.transformer,
            torch_dtype=dtype,
            device=load_device,
        )

    pipe = FluxPipeline.from_pretrained(args.base_model, transformer=transformer, torch_dtype=dtype)

    if args.offload:
        enable_sequential_offload(pipe, args.device)
    else:
        pipe = pipe.to(args.device)

    lower_route = f"{args.base_model} {args.transformer}".lower()
    steps = args.steps if args.steps is not None else (4 if "schnell" in lower_route else 20)
    guidance_scale = args.guidance_scale if args.guidance_scale is not None else (0.0 if "schnell" in lower_route else 3.5)

    forward_kwargs = {
        "prompt": args.prompt,
        "num_inference_steps": steps,
        "guidance_scale": guidance_scale,
    }
    if args.height is not None:
        forward_kwargs["height"] = args.height
    if args.width is not None:
        forward_kwargs["width"] = args.width
    if args.seed is not None:
        forward_kwargs["generator"] = torch.Generator(device=args.device if not args.offload else "cpu").manual_seed(args.seed)

    result = pipe(**forward_kwargs)
    image = result.images[0]

    output = Path(args.output).expanduser()
    if output.parent and str(output.parent) != ".":
        output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    print(f"saved {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
