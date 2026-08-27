#!/usr/bin/env python3
"""Janus / Janus-Pro text-to-image helper.

Safe default: prints a dry-run plan. Add --run-model to download/load the
model and generate images.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Sequence


def _roles(family: str) -> tuple[str, str]:
    if family == "janus-pro":
        return ("<|User|>", "<|Assistant|>")
    return ("User", "Assistant")


def _dry_run(args: argparse.Namespace) -> int:
    plan = {
        "family": args.family,
        "model_id": args.model_id,
        "prompt": args.prompt,
        "roles": list(_roles(args.family)),
        "output_dir": args.output_dir,
        "parallel_size": args.parallel_size,
        "temperature": args.temperature,
        "cfg_weight": args.cfg_weight,
        "image_token_num": args.image_token_num,
        "img_size": args.img_size,
        "patch_size": args.patch_size,
        "seed": args.seed,
        "device": args.device,
        "dtype": args.dtype,
        "run_model": False,
    }
    print("Janus text-to-image dry run")
    print(json.dumps(plan, indent=2, sort_keys=True))
    print("\nAdd --run-model only after model access, CUDA/VRAM, and output path are ready.")
    return 0


def _resolve_device(torch_module, requested: str, allow_cpu: bool) -> str:
    if requested == "auto":
        device = "cuda" if torch_module.cuda.is_available() else "cpu"
    else:
        device = requested
    if device == "cuda" and not torch_module.cuda.is_available():
        raise SystemExit("CUDA was requested but torch.cuda.is_available() is false.")
    if device == "cpu" and not allow_cpu:
        raise SystemExit("Real Janus generation is normally CUDA-oriented. Pass --allow-cpu if you intentionally want a very slow CPU experiment.")
    return device


def _resolve_dtype(torch_module, name: str, device: str):
    if name == "auto":
        return torch_module.bfloat16 if device == "cuda" else torch_module.float32
    return {
        "bfloat16": torch_module.bfloat16,
        "float16": torch_module.float16,
        "float32": torch_module.float32,
    }[name]


def _run_model(args: argparse.Namespace) -> int:
    if args.img_size % args.patch_size != 0:
        raise SystemExit("--img-size must be divisible by --patch-size")
    if args.parallel_size <= 0:
        raise SystemExit("--parallel-size must be positive")

    import numpy as np
    import PIL.Image
    import torch
    from transformers import AutoModelForCausalLM
    from janus.models import VLChatProcessor

    device = _resolve_device(torch, args.device, args.allow_cpu)
    dtype = _resolve_dtype(torch, args.dtype, device)
    if args.seed is not None:
        torch.manual_seed(args.seed)
        np.random.seed(args.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(args.seed)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    user_role, assistant_role = _roles(args.family)
    vl_chat_processor = VLChatProcessor.from_pretrained(args.model_id)
    tokenizer = vl_chat_processor.tokenizer
    vl_gpt = AutoModelForCausalLM.from_pretrained(args.model_id, trust_remote_code=True)
    vl_gpt = vl_gpt.to(dtype=dtype)
    if device == "cuda":
        vl_gpt = vl_gpt.cuda().eval()
    else:
        vl_gpt = vl_gpt.to(device).eval()

    conversation = [{"role": user_role, "content": args.prompt}, {"role": assistant_role, "content": ""}]
    sft_format = vl_chat_processor.apply_sft_template_for_multi_turn_prompts(
        conversations=conversation,
        sft_format=vl_chat_processor.sft_format,
        system_prompt="",
    )
    full_prompt = sft_format + vl_chat_processor.image_start_tag
    input_ids = torch.LongTensor(tokenizer.encode(full_prompt)).to(device)

    tokens = torch.zeros((args.parallel_size * 2, len(input_ids)), dtype=torch.int, device=device)
    for i in range(args.parallel_size * 2):
        tokens[i, :] = input_ids
        if i % 2 != 0:
            tokens[i, 1:-1] = vl_chat_processor.pad_id

    inputs_embeds = vl_gpt.language_model.get_input_embeddings()(tokens)
    generated_tokens = torch.zeros((args.parallel_size, args.image_token_num), dtype=torch.int, device=device)
    past_key_values = None

    with torch.inference_mode():
        for idx in range(args.image_token_num):
            outputs = vl_gpt.language_model.model(
                inputs_embeds=inputs_embeds,
                use_cache=True,
                past_key_values=past_key_values,
            )
            past_key_values = outputs.past_key_values
            hidden_states = outputs.last_hidden_state
            logits = vl_gpt.gen_head(hidden_states[:, -1, :])
            logit_cond = logits[0::2, :]
            logit_uncond = logits[1::2, :]
            logits = logit_uncond + args.cfg_weight * (logit_cond - logit_uncond)
            probs = torch.softmax(logits / args.temperature, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            generated_tokens[:, idx] = next_token.squeeze(dim=-1)
            next_token = torch.cat([next_token.unsqueeze(1), next_token.unsqueeze(1)], dim=1).reshape(-1)
            img_embeds = vl_gpt.prepare_gen_img_embeds(next_token)
            inputs_embeds = img_embeds.unsqueeze(1)

        decoded = vl_gpt.gen_vision_model.decode_code(
            generated_tokens.to(dtype=torch.int),
            shape=[args.parallel_size, 8, args.img_size // args.patch_size, args.img_size // args.patch_size],
        )

    decoded = decoded.to(torch.float32).cpu().numpy().transpose(0, 2, 3, 1)
    decoded = np.clip((decoded + 1) / 2 * 255, 0, 255).astype(np.uint8)

    for idx, array in enumerate(decoded):
        path = output_dir / f"janus_{args.family}_{idx:02d}.jpg"
        PIL.Image.fromarray(array).save(path)
        print(path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dry-run or execute Janus / Janus-Pro text-to-image generation.")
    parser.add_argument("--family", choices=["janus", "janus-pro"], default="janus", help="Model family to use.")
    parser.add_argument("--model-id", default="deepseek-ai/Janus-1.3B", help="Hugging Face model id.")
    parser.add_argument("--prompt", required=True, help="Text prompt to generate from.")
    parser.add_argument("--output-dir", default="generated_samples", help="Directory for generated images.")
    parser.add_argument("--parallel-size", type=int, default=5, help="Number of images to sample in parallel.")
    parser.add_argument("--temperature", type=float, default=1.0, help="Sampling temperature.")
    parser.add_argument("--cfg-weight", type=float, default=5.0, help="Classifier-free guidance weight.")
    parser.add_argument("--image-token-num", type=int, default=576, help="Image tokens per image.")
    parser.add_argument("--img-size", type=int, default=384, help="Generated image size before optional resizing.")
    parser.add_argument("--patch-size", type=int, default=16, help="Decoder patch size.")
    parser.add_argument("--seed", type=int, default=None, help="Optional RNG seed.")
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto", help="Execution device.")
    parser.add_argument("--dtype", choices=["auto", "bfloat16", "float16", "float32"], default="auto", help="Model dtype.")
    parser.add_argument("--allow-cpu", action="store_true", help="Allow an explicit slow CPU real-model run.")
    parser.add_argument("--run-model", action="store_true", help="Download/load the model and generate images.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.run_model:
        return _dry_run(args)
    return _run_model(args)


if __name__ == "__main__":
    raise SystemExit(main())
