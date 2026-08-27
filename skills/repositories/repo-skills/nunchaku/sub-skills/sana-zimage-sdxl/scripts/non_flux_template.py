#!/usr/bin/env python3
"""Parameterized Nunchaku template for Sana, Z-Image, SDXL, and SDXL-Turbo.

This script intentionally requires explicit model assets. It never chooses the
repository example defaults on behalf of the caller.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a bounded text-to-image smoke with a Nunchaku non-FLUX replacement. "
            "Requires explicit Diffusers base model and Nunchaku quantized asset."
        )
    )
    parser.add_argument("--family", choices=("sana", "zimage", "sdxl"), required=True)
    parser.add_argument(
        "--base-model",
        required=True,
        help="Diffusers base model ID or local directory, for example a Sana, Z-Image, SDXL, or SDXL-Turbo base.",
    )
    parser.add_argument(
        "--quantized-path",
        required=True,
        help="Local file or Hub-style path to a Nunchaku .safetensors/.sft asset. No default is provided.",
    )
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", required=True, help="Output image path to write.")
    parser.add_argument("--device", default="cuda", help="Target device for full pipeline placement; default: cuda.")
    parser.add_argument("--dtype", choices=("auto", "bfloat16", "float16"), default="auto")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--steps", type=int, default=None, help="Inference steps. If omitted, family defaults are used.")
    parser.add_argument(
        "--guidance-scale", type=float, default=None, help="Guidance scale. If omitted, family defaults are used."
    )
    parser.add_argument(
        "--sdxl-variant",
        choices=("base", "turbo"),
        default="base",
        help="Select SDXL base or SDXL-Turbo generation defaults when --family sdxl.",
    )
    parser.add_argument(
        "--pag-layer",
        type=int,
        default=None,
        help="For Sana only: enable SanaPAGPipeline and load this PAG layer into the Nunchaku transformer.",
    )
    parser.add_argument(
        "--pag-scale",
        type=float,
        default=2.0,
        help="For Sana PAG only: PAG scale passed to the pipeline.",
    )
    parser.add_argument(
        "--pag-applied-layers",
        default=None,
        help="For Sana PAG only: Diffusers pag_applied_layers string. Defaults to transformer_blocks.<pag-layer>.",
    )
    parser.add_argument(
        "--precision",
        choices=("auto", "int4", "fp4"),
        default="auto",
        help="Passed to the Sana loader. Z-Image/SDXL infer precision from the installed Nunchaku utilities and asset metadata.",
    )
    parser.add_argument(
        "--sequential-cpu-offload",
        action="store_true",
        help="For Z-Image only: call pipe.enable_sequential_cpu_offload() instead of pipe.to(device).",
    )
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="Pass local_files_only=True to Diffusers pipeline loading. Quantized Hub paths may still be resolved by Nunchaku loaders.",
    )
    parser.add_argument("--revision", default=None, help="Optional Diffusers base model revision.")
    parser.add_argument(
        "--token-env",
        default=None,
        help="Optional environment variable name containing a Hugging Face token. The token value is never printed.",
    )
    return parser


def _is_probable_hub_file(path_text: str) -> bool:
    path = Path(path_text)
    return (not path.is_absolute()) and len(path.parts) >= 3 and path.name.endswith((".safetensors", ".sft"))


def _validate_asset_path(path_text: str) -> None:
    path = Path(path_text).expanduser()
    if path.exists():
        if not path.is_file():
            raise SystemExit(f"--quantized-path exists but is not a file: {path}")
        if not path.name.endswith((".safetensors", ".sft")):
            raise SystemExit("--quantized-path must be a .safetensors or .sft file for this template")
        return
    if _is_probable_hub_file(path_text):
        return
    raise SystemExit(
        "--quantized-path must be an existing local .safetensors/.sft file or a Hub-style path "
        "including the filename, such as org/repo/file.safetensors"
    )


def _validate_family_asset_hint(family: str, variant: str, quantized_path: str) -> None:
    name = Path(quantized_path).name.lower()
    if not name.endswith((".safetensors", ".sft")):
        return
    hints = {
        "sana": ("sana",),
        "zimage": ("z-image", "zimage"),
        "sdxl": ("sdxl",),
    }
    forbidden = {
        "sana": ("z-image", "zimage", "sdxl", "flux", "qwen"),
        "zimage": ("sana", "sdxl", "flux", "qwen"),
        "sdxl": ("sana", "z-image", "zimage", "flux", "qwen"),
    }
    if any(token in name for token in forbidden[family]) and not any(token in name for token in hints[family]):
        raise SystemExit(f"quantized asset name looks inconsistent with --family {family!r}: {name}")
    if family == "sdxl" and variant == "turbo" and "sdxl" in name and "turbo" not in name:
        print("warning: --sdxl-variant turbo selected but asset name does not contain 'turbo'", file=sys.stderr)
    if family == "sdxl" and variant == "base" and "sdxl-turbo" in name:
        print("warning: --sdxl-variant base selected but asset name looks like SDXL-Turbo", file=sys.stderr)


def _torch_dtype(dtype_arg: str, family: str) -> Any:
    import torch

    if dtype_arg == "bfloat16":
        return torch.bfloat16
    if dtype_arg == "float16":
        return torch.float16
    # Native Z-Image examples use fp16 on Turing and bf16 otherwise.
    if family == "zimage" and torch.cuda.is_available():
        capability = torch.cuda.get_device_capability()
        if capability == (7, 5):
            return torch.float16
    return torch.bfloat16


def _warn_known_unverified_paths(family: str, dtype: Any) -> None:
    import torch

    if not torch.cuda.is_available():
        return
    capability = torch.cuda.get_device_capability()
    if family in {"sana", "sdxl"} and capability == (7, 5):
        print(
            "warning: native Sana/SDXL verification candidates skip Turing GPUs; treat this path as unverified",
            file=sys.stderr,
        )
    if family in {"sana", "sdxl"} and dtype is torch.float16:
        print(
            "warning: native Sana/SDXL examples use bfloat16; float16 should be separately validated",
            file=sys.stderr,
        )


def _base_load_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    if args.local_files_only:
        kwargs["local_files_only"] = True
    if args.revision:
        kwargs["revision"] = args.revision
    if args.token_env:
        token = os.environ.get(args.token_env)
        if not token:
            raise SystemExit(f"--token-env was set but environment variable {args.token_env!r} is empty or missing")
        kwargs["token"] = token
    return kwargs


def _defaults(args: argparse.Namespace) -> tuple[int, float]:
    if args.family == "sana":
        return (20 if args.steps is None else args.steps, (5.0 if args.pag_layer is not None else 4.5) if args.guidance_scale is None else args.guidance_scale)
    if args.family == "zimage":
        return (8 if args.steps is None else args.steps, 0.0 if args.guidance_scale is None else args.guidance_scale)
    # SDXL
    if args.sdxl_variant == "turbo":
        return (4 if args.steps is None else args.steps, 0.0 if args.guidance_scale is None else args.guidance_scale)
    return (50 if args.steps is None else args.steps, 5.0 if args.guidance_scale is None else args.guidance_scale)


def _generator(seed: int, device: str) -> Any:
    import torch

    if device.startswith("cuda") and torch.cuda.is_available():
        return torch.Generator(device="cuda").manual_seed(seed)
    return torch.Generator().manual_seed(seed)


def _run_sana(args: argparse.Namespace, dtype: Any, steps: int, guidance: float) -> Any:
    import torch
    from nunchaku import NunchakuSanaTransformer2DModel

    load_kwargs = _base_load_kwargs(args)
    if args.pag_layer is None:
        from diffusers import SanaPipeline

        transformer = NunchakuSanaTransformer2DModel.from_pretrained(
            args.quantized_path,
            device=args.device,
            precision=args.precision,
        )
        pipe = SanaPipeline.from_pretrained(
            args.base_model,
            transformer=transformer,
            variant="bf16" if dtype is torch.bfloat16 else None,
            torch_dtype=dtype,
            **load_kwargs,
        ).to(args.device)
        if hasattr(pipe, "vae"):
            pipe.vae.to(dtype)
        if hasattr(pipe, "text_encoder"):
            pipe.text_encoder.to(dtype)
        return pipe(
            prompt=args.prompt,
            height=args.height,
            width=args.width,
            guidance_scale=guidance,
            num_inference_steps=steps,
            generator=_generator(args.seed, args.device),
        ).images[0]

    from diffusers import SanaPAGPipeline

    pag_applied_layers = args.pag_applied_layers or f"transformer_blocks.{args.pag_layer}"
    transformer = NunchakuSanaTransformer2DModel.from_pretrained(
        args.quantized_path,
        device=args.device,
        precision=args.precision,
        pag_layers=args.pag_layer,
    )
    pipe = SanaPAGPipeline.from_pretrained(
        args.base_model,
        transformer=transformer,
        variant="bf16" if dtype is torch.bfloat16 else None,
        torch_dtype=dtype,
        pag_applied_layers=pag_applied_layers,
        **load_kwargs,
    ).to(args.device)
    # Native Sana PAG example preserves the Nunchaku quantized blocks by avoiding
    # Diffusers' PAG attention processor reset. Re-check this line after Diffusers upgrades.
    pipe._set_pag_attn_processor = lambda *unused_args, **unused_kwargs: None
    if hasattr(pipe, "vae"):
        pipe.vae.to(dtype)
    if hasattr(pipe, "text_encoder"):
        pipe.text_encoder.to(dtype)
    return pipe(
        prompt=args.prompt,
        height=args.height,
        width=args.width,
        guidance_scale=guidance,
        pag_scale=args.pag_scale,
        num_inference_steps=steps,
        generator=_generator(args.seed, args.device),
    ).images[0]


def _run_zimage(args: argparse.Namespace, dtype: Any, steps: int, guidance: float) -> Any:
    try:
        from diffusers import ZImagePipeline
    except ImportError:
        from diffusers.pipelines.z_image.pipeline_z_image import ZImagePipeline
    from nunchaku import NunchakuZImageTransformer2DModel

    load_kwargs = _base_load_kwargs(args)
    transformer = NunchakuZImageTransformer2DModel.from_pretrained(args.quantized_path, torch_dtype=dtype)
    pipe = ZImagePipeline.from_pretrained(
        args.base_model,
        transformer=transformer,
        torch_dtype=dtype,
        low_cpu_mem_usage=False,
        **load_kwargs,
    )
    if args.sequential_cpu_offload:
        pipe.enable_sequential_cpu_offload()
    else:
        pipe = pipe.to(args.device)
    return pipe(
        prompt=args.prompt,
        height=args.height,
        width=args.width,
        num_inference_steps=steps,
        guidance_scale=guidance,
        generator=_generator(args.seed, args.device),
    ).images[0]


def _run_sdxl(args: argparse.Namespace, dtype: Any, steps: int, guidance: float) -> Any:
    from diffusers import StableDiffusionXLPipeline
    from nunchaku.models.unets.unet_sdxl import NunchakuSDXLUNet2DConditionModel

    load_kwargs = _base_load_kwargs(args)
    unet = NunchakuSDXLUNet2DConditionModel.from_pretrained(args.quantized_path, torch_dtype=dtype)
    pipe_kwargs: dict[str, Any] = {
        "unet": unet,
        "torch_dtype": dtype,
        "variant": "fp16",
        **load_kwargs,
    }
    if args.sdxl_variant == "base":
        pipe_kwargs["use_safetensors"] = True
    pipe = StableDiffusionXLPipeline.from_pretrained(args.base_model, **pipe_kwargs).to(args.device)
    return pipe(
        prompt=args.prompt,
        height=args.height,
        width=args.width,
        guidance_scale=guidance,
        num_inference_steps=steps,
        generator=_generator(args.seed, args.device),
    ).images[0]


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    _validate_asset_path(args.quantized_path)
    _validate_family_asset_hint(args.family, args.sdxl_variant, args.quantized_path)

    if args.pag_layer is not None and args.family != "sana":
        parser.error("--pag-layer is only valid with --family sana")
    if args.sequential_cpu_offload and args.family != "zimage":
        parser.error("--sequential-cpu-offload is only supported by this template for --family zimage")

    import torch

    if args.device.startswith("cuda") and not torch.cuda.is_available():
        raise SystemExit("CUDA was requested but torch.cuda.is_available() is false")
    if args.family == "sana" and not args.device.startswith("cuda"):
        raise SystemExit("Sana Nunchaku loading requires a CUDA device")

    dtype = _torch_dtype(args.dtype, args.family)
    _warn_known_unverified_paths(args.family, dtype)
    steps, guidance = _defaults(args)

    if args.family == "sana":
        image = _run_sana(args, dtype, steps, guidance)
    elif args.family == "zimage":
        image = _run_zimage(args, dtype, steps, guidance)
    else:
        image = _run_sdxl(args, dtype, steps, guidance)

    output_path = Path(args.output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    print(f"saved image to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
