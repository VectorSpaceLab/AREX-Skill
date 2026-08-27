#!/usr/bin/env python3
"""Safer SUPIR batch restoration wrapper.

Default behavior is a dry run: validate folders, summarize options, and print
what would be executed. Pass --run to load models and perform restoration.
This script assumes the SUPIR/sgm packages are importable in the active
environment. LLaVA is imported only when captioning is enabled. Run from an
environment where the SUPIR source packages are installed or on PYTHONPATH.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable, List

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
DEFAULT_A_PROMPT = (
    "Cinematic, High Contrast, highly detailed, taken using a Canon EOS R camera, "
    "hyper detailed photo - realistic maximum detail, 32k, Color Grading, ultra HD, "
    "extreme meticulous detailing, skin pore detailing, hyper sharpness, perfect without deformations."
)
DEFAULT_N_PROMPT = (
    "painting, oil painting, illustration, drawing, art, sketch, oil painting, cartoon, "
    "CG Style, 3D render, unreal engine, blurring, dirty, messy, worst quality, low quality, "
    "frames, watermark, signature, jpeg artifacts, deformed, lowres, over-smooth"
)


def _images(path: Path) -> List[Path]:
    if not path.exists() or not path.is_dir():
        return []
    return sorted(p for p in path.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS)


def _resolve_llava_path(explicit: str | None) -> str:
    if explicit:
        return explicit
    env_value = os.environ.get("SUPIR_LLAVA_MODEL_PATH")
    if env_value:
        return env_value
    try:
        from CKPT_PTH import LLAVA_MODEL_PATH  # type: ignore
    except Exception as exc:  # pragma: no cover - host-specific
        raise SystemExit(
            "LLaVA is enabled but no model path was provided. Pass --llava_model_path, "
            "set SUPIR_LLAVA_MODEL_PATH, or provide a CKPT_PTH.py module with LLAVA_MODEL_PATH. "
            f"Original error: {type(exc).__name__}: {exc}"
        )
    return LLAVA_MODEL_PATH


def _device_plan() -> tuple[str, str]:
    import torch

    count = torch.cuda.device_count()
    if count >= 2:
        return "cuda:0", "cuda:1"
    if count == 1:
        return "cuda:0", "cuda:0"
    raise SystemExit("SUPIR batch restoration is CUDA-only; torch.cuda.device_count() is 0")


def _print_plan(args: argparse.Namespace, imgs: Iterable[Path]) -> None:
    imgs = list(imgs)
    print("# SUPIR batch plan")
    print(f"config: {args.config or '<required for --run>'}")
    print(f"img_dir: {args.img_dir}")
    print(f"save_dir: {args.save_dir}")
    print(f"images: {len(imgs)}")
    for p in imgs[:10]:
        print(f"  - {p.name}")
    if len(imgs) > 10:
        print(f"  ... {len(imgs) - 10} more")
    print(f"SUPIR_sign: {args.SUPIR_sign}")
    print(f"upscale/min_size: {args.upscale}/{args.min_size}")
    print(f"steps/seed/samples: {args.edm_steps}/{args.seed}/{args.num_samples}")
    print(f"llava: {'disabled' if args.no_llava else 'enabled'}")
    print(f"tile_vae: {args.use_tile_vae} encoder={args.encoder_tile_size} decoder={args.decoder_tile_size}")
    print(f"dtype ae/diff: {args.ae_dtype}/{args.diff_dtype}")
    print(f"color_fix_type: {args.color_fix_type}")
    print("mode: RUN" if args.run else "mode: DRY-RUN")


def run(args: argparse.Namespace, imgs: List[Path]) -> None:
    if not args.config:
        raise SystemExit("--config is required when --run is used")
    if not imgs:
        raise SystemExit("No supported input images found")

    import torch
    from PIL import Image
    from SUPIR.util import PIL2Tensor, Tensor2PIL, convert_dtype, create_SUPIR_model

    supir_device, llava_device = _device_plan()
    print(f"SUPIR_device={supir_device} LLaVA_device={llava_device}")

    model = create_SUPIR_model(args.config, SUPIR_sign=args.SUPIR_sign)
    if args.loading_half_params:
        model = model.half()
    if args.use_tile_vae:
        model.init_tile_vae(encoder_tile_size=args.encoder_tile_size, decoder_tile_size=args.decoder_tile_size)
    model.ae_dtype = convert_dtype(args.ae_dtype)
    model.model.dtype = convert_dtype(args.diff_dtype)
    model = model.to(supir_device)

    use_llava = not args.no_llava
    llava_agent = None
    if use_llava:
        from llava.llava_agent import LLavaAgent

        llava_agent = LLavaAgent(
            _resolve_llava_path(args.llava_model_path),
            device=llava_device,
            load_8bit=args.load_8bit_llava,
            load_4bit=False,
        )

    args.save_dir.mkdir(parents=True, exist_ok=True)
    for img_path in imgs:
        stem = img_path.stem
        print(f"processing {img_path.name}")
        with Image.open(img_path) as pil:
            pil = pil.convert("RGB")
            lq_img, h0, w0 = PIL2Tensor(pil, upsacle=args.upscale, min_size=args.min_size)
            lq_img = lq_img.unsqueeze(0).to(supir_device)[:, :3, :, :]

            preview, h1, w1 = PIL2Tensor(pil, upsacle=args.upscale, min_size=args.min_size, fix_resize=512)
            preview = preview.unsqueeze(0).to(supir_device)[:, :3, :, :]
            clean = model.batchify_denoise(preview)
            clean_pil = Tensor2PIL(clean[0], h1, w1)

            captions = llava_agent.gen_image_caption([clean_pil]) if llava_agent else [args.manual_caption or ""]
            print("caption:", captions[0])

            samples = model.batchify_sample(
                lq_img,
                captions,
                num_steps=args.edm_steps,
                restoration_scale=args.s_stage1,
                s_churn=args.s_churn,
                s_noise=args.s_noise,
                cfg_scale=args.s_cfg,
                control_scale=args.s_stage2,
                seed=args.seed,
                num_samples=args.num_samples,
                p_p=args.a_prompt,
                n_p=args.n_prompt,
                color_fix_type=args.color_fix_type,
                use_linear_CFG=args.linear_CFG,
                use_linear_control_scale=args.linear_s_stage2,
                cfg_scale_start=args.spt_linear_CFG,
                control_scale_start=args.spt_linear_s_stage2,
            )
            for i, sample in enumerate(samples):
                out = args.save_dir / f"{stem}_{i}.png"
                Tensor2PIL(sample, h0, w0).save(out)
                print("saved", out)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SUPIR batch restoration wrapper with safe dry-run default.")
    parser.add_argument("--config", type=str, help="SUPIR YAML config with resolved checkpoint paths. Required for --run.")
    parser.add_argument("--img_dir", type=Path, required=True)
    parser.add_argument("--save_dir", type=Path, required=True)
    parser.add_argument("--upscale", type=int, default=1)
    parser.add_argument("--SUPIR_sign", type=str, default="Q", choices=["F", "Q"])
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--min_size", type=int, default=1024)
    parser.add_argument("--edm_steps", type=int, default=50)
    parser.add_argument("--s_stage1", type=float, default=-1.0)
    parser.add_argument("--s_churn", type=float, default=5.0)
    parser.add_argument("--s_noise", type=float, default=1.01)
    parser.add_argument("--s_cfg", type=float, default=4.0)
    parser.add_argument("--s_stage2", type=float, default=1.0)
    parser.add_argument("--num_samples", type=int, default=1)
    parser.add_argument("--a_prompt", type=str, default=DEFAULT_A_PROMPT)
    parser.add_argument("--n_prompt", type=str, default=DEFAULT_N_PROMPT)
    parser.add_argument("--manual_caption", type=str, default="", help="Caption to use when --no_llava is set.")
    parser.add_argument("--color_fix_type", type=str, default="Wavelet", choices=["None", "AdaIn", "Wavelet"])
    parser.add_argument("--linear_CFG", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--linear_s_stage2", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--spt_linear_CFG", type=float, default=1.0)
    parser.add_argument("--spt_linear_s_stage2", type=float, default=0.0)
    parser.add_argument("--ae_dtype", type=str, default="bf16", choices=["fp32", "bf16"])
    parser.add_argument("--diff_dtype", type=str, default="fp16", choices=["fp32", "fp16", "bf16"])
    parser.add_argument("--no_llava", action="store_true", default=False)
    parser.add_argument("--llava_model_path", type=str, help="Explicit LLaVA model path; otherwise SUPIR_LLAVA_MODEL_PATH or CKPT_PTH.LLAVA_MODEL_PATH is used.")
    parser.add_argument("--loading_half_params", action="store_true", default=False)
    parser.add_argument("--use_tile_vae", action="store_true", default=False)
    parser.add_argument("--encoder_tile_size", type=int, default=512)
    parser.add_argument("--decoder_tile_size", type=int, default=64)
    parser.add_argument("--load_8bit_llava", action="store_true", default=False)
    parser.add_argument("--dry-run", action="store_true", help="Explicit dry-run marker; default unless --run is passed.")
    parser.add_argument("--run", action="store_true", help="Actually load models and restore images.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.dry_run and args.run:
        parser.error("choose --dry-run or --run, not both")
    imgs = _images(args.img_dir)
    _print_plan(args, imgs)
    if not args.img_dir.exists() or not args.img_dir.is_dir():
        raise SystemExit(f"input directory not found: {args.img_dir}")
    if args.num_samples > 1 and len(imgs) != 1:
        raise SystemExit("num_samples > 1 mirrors SUPIRModel behavior and requires exactly one input image")
    if args.run:
        run(args, imgs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
