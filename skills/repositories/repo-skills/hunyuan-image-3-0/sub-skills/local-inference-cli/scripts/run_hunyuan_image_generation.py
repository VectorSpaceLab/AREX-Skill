#!/usr/bin/env python3
"""Self-contained HunyuanImage-3.0 generation runner for the repo skill.

This script adapts the inspected local generation CLI into a skill-owned entry
point. It imports the installed HunyuanImage-3.0 package and does not import the
original repository checkout script. Use --dry-run to validate arguments without
loading model weights or touching CUDA.
"""

from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("Skill-owned HunyuanImage-3.0 generation runner")
    parser.add_argument("--prompt", type=str, required=True, help="Prompt to run")
    parser.add_argument(
        "--image",
        type=str,
        default=None,
        help="One image path or comma-separated image paths for conditioning",
    )
    parser.add_argument("--max_new_tokens", type=int, default=2048)
    parser.add_argument("--model-id", type=str, required=True, help="Local model checkpoint directory")
    parser.add_argument("--attn-impl", type=str, default="sdpa", choices=["sdpa", "flash_attention_2"])
    parser.add_argument("--moe-impl", type=str, default="eager", choices=["eager", "flashinfer"])
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--diff-infer-steps", type=int, default=50)
    parser.add_argument("--image-size", type=str, default="auto")
    parser.add_argument(
        "--use-system-prompt",
        type=str,
        choices=["None", "dynamic", "en_vanilla", "en_recaption", "en_think_recaption", "en_unified", "custom"],
        default=None,
    )
    parser.add_argument("--system-prompt", type=str, default=None)
    parser.add_argument("--bot-task", type=str, choices=["image", "auto", "recaption", "think_recaption"], default=None)
    parser.add_argument("--save", type=str, default="image.png")
    parser.add_argument("--verbose", type=int, default=2)
    parser.add_argument("--rewrite", action="store_true", help="Use Tencent Cloud DeepSeek prompt rewrite before generation")
    parser.add_argument(
        "--sys-deepseek-prompt",
        choices=["universal", "text_rendering"],
        default="universal",
        help="DeepSeek PE prompt family. Added by the skill runner to avoid the source parser mismatch.",
    )
    parser.add_argument("--reproduce", action="store_true")
    parser.add_argument("--infer-align-image-size", action="store_true")
    parser.add_argument("--use-taylor-cache", action="store_true")
    parser.add_argument("--taylor-cache-interval", type=int, default=5)
    parser.add_argument("--taylor-cache-order", type=int, default=2)
    parser.add_argument("--taylor-cache-enable-first-enhance", action="store_true")
    parser.add_argument("--taylor-cache-first-enhance-steps", type=int, default=3)
    parser.add_argument("--taylor-cache-enable-tailing-enhance", action="store_true")
    parser.add_argument("--taylor-cache-tailing-enhance-steps", type=int, default=1)
    parser.add_argument("--taylor-cache-low-freqs-order", type=int, default=2)
    parser.add_argument("--taylor-cache-high-freqs-order", type=int, default=2)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate arguments and print the call plan without importing the model or loading weights.",
    )
    return parser


def parse_image_arg(value: str | None) -> str | list[str] | None:
    if value is None:
        return None
    paths = [part.strip() for part in value.split(",") if part.strip()]
    if not paths:
        return None
    if len(paths) == 1:
        return paths[0]
    return paths


def set_reproducibility(enable: bool, global_seed: int | None = None, benchmark: bool | None = None) -> None:
    if not enable:
        return
    import numpy as np
    import torch

    random.seed(global_seed)
    np.random.seed(global_seed)
    torch.manual_seed(global_seed)
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    torch.backends.cudnn.benchmark = (not enable) if benchmark is None else benchmark
    torch.backends.cudnn.deterministic = enable
    torch.use_deterministic_algorithms(enable)


def rewrite_prompt(args: argparse.Namespace) -> str:
    key_id = os.getenv("DEEPSEEK_KEY_ID")
    key_secret = os.getenv("DEEPSEEK_KEY_SECRET")
    if not key_id or not key_secret:
        raise SystemExit("--rewrite requires DEEPSEEK_KEY_ID and DEEPSEEK_KEY_SECRET")

    try:
        from PE.deepseek import DeepSeekClient
        from PE.system_prompt import system_prompt_text_rendering, system_prompt_universal
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"DeepSeek PE modules are not importable: {type(exc).__name__}: {exc}") from exc

    system_prompt = {
        "universal": system_prompt_universal,
        "text_rendering": system_prompt_text_rendering,
    }[args.sys_deepseek_prompt]
    prompt, _reason = DeepSeekClient(key_id, key_secret).run_single_recaption(system_prompt, args.prompt)
    return prompt


def call_plan(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "model_id": args.model_id,
        "prompt": args.prompt,
        "image": parse_image_arg(args.image),
        "save": args.save,
        "attn_implementation": args.attn_impl,
        "moe_impl": args.moe_impl,
        "seed": args.seed,
        "image_size": args.image_size,
        "use_system_prompt": args.use_system_prompt,
        "system_prompt_supplied": bool(args.system_prompt),
        "bot_task": args.bot_task,
        "diff_infer_steps": args.diff_infer_steps,
        "infer_align_image_size": args.infer_align_image_size,
        "use_taylor_cache": args.use_taylor_cache,
        "rewrite": args.rewrite,
        "reproduce": args.reproduce,
    }


def validate_args(args: argparse.Namespace) -> None:
    if not args.prompt:
        raise SystemExit("--prompt is required")
    model_path = Path(args.model_id).expanduser()
    if not args.dry_run and not model_path.exists():
        raise SystemExit(f"Model path does not exist: {args.model_id}")
    if args.use_system_prompt == "custom" and not args.system_prompt:
        raise SystemExit("--use-system-prompt custom requires --system-prompt")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(args)

    if args.dry_run:
        print(json.dumps(call_plan(args), ensure_ascii=False, indent=2))
        return 0

    if args.reproduce:
        set_reproducibility(args.reproduce, global_seed=args.seed)

    if args.rewrite:
        args.prompt = rewrite_prompt(args)
        print(f"rewrite prompt: {args.prompt}")

    from hunyuan_image_3 import HunyuanImage3ForCausalMM

    import_kwargs = {
        "attn_implementation": args.attn_impl,
        "torch_dtype": "auto",
        "device_map": "auto",
        "moe_impl": args.moe_impl,
        "moe_drop_tokens": True,
    }
    model = HunyuanImage3ForCausalMM.from_pretrained(args.model_id, **import_kwargs)
    model.load_tokenizer(args.model_id)

    cot_text, samples = model.generate_image(
        prompt=args.prompt,
        seed=args.seed,
        image_size=args.image_size,
        use_system_prompt=args.use_system_prompt,
        system_prompt=args.system_prompt,
        bot_task=args.bot_task,
        diff_infer_steps=args.diff_infer_steps,
        verbose=args.verbose,
        max_new_tokens=args.max_new_tokens,
        image=parse_image_arg(args.image),
        infer_align_image_size=args.infer_align_image_size,
        use_taylor_cache=args.use_taylor_cache,
        taylor_cache_interval=args.taylor_cache_interval,
        taylor_cache_order=args.taylor_cache_order,
        taylor_cache_enable_first_enhance=args.taylor_cache_enable_first_enhance,
        taylor_cache_first_enhance_steps=args.taylor_cache_first_enhance_steps,
        taylor_cache_enable_tailing_enhance=args.taylor_cache_enable_tailing_enhance,
        taylor_cache_tailing_enhance_steps=args.taylor_cache_tailing_enhance_steps,
        taylor_cache_low_freqs_order=args.taylor_cache_low_freqs_order,
        taylor_cache_high_freqs_order=args.taylor_cache_high_freqs_order,
    )
    Path(args.save).parent.mkdir(parents=True, exist_ok=True)
    samples[0].save(args.save)
    if cot_text:
        print(f"cot_text: {cot_text}")
    print(f"Image saved to {args.save}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
