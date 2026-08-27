#!/usr/bin/env python3
"""JanusFlow rectified-flow text-to-image helper.

Safe default: prints a dry-run plan. Add --run-model to download/load the
model and generate images.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence


def _dry_run(args: argparse.Namespace) -> int:
    plan = {
        "model_id": args.model_id,
        "prompt": args.prompt,
        "output_dir": args.output_dir,
        "cfg_weight": args.cfg_weight,
        "num_inference_steps": args.num_inference_steps,
        "batch_size": args.batch_size,
        "seed": args.seed,
        "device": args.device,
        "dtype": args.dtype,
        "allow_cpu": args.allow_cpu,
        "run_model": False,
    }
    print("JanusFlow text-to-image dry run")
    print(json.dumps(plan, indent=2, sort_keys=True))
    print("\nAdd --run-model only after you confirm diffusers compatibility, CUDA, and SDXL VAE access.")
    return 0


def _resolve_device(torch_module, requested: str, allow_cpu: bool) -> str:
    if requested == "auto":
        device = "cuda" if torch_module.cuda.is_available() else "cpu"
    else:
        device = requested
    if device == "cuda" and not torch_module.cuda.is_available():
        raise SystemExit("CUDA was requested but torch.cuda.is_available() is false.")
    if device == "cpu" and not allow_cpu:
        raise SystemExit("Real JanusFlow generation is normally CUDA-oriented. Pass --allow-cpu if you intentionally want a slow CPU experiment.")
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
    import numpy as np
    import PIL.Image
    import torch
    import torchvision
    from diffusers.models import AutoencoderKL
    from janus.janusflow.models import MultiModalityCausalLM, VLChatProcessor

    device = _resolve_device(torch, args.device, args.allow_cpu)
    dtype = _resolve_dtype(torch, args.dtype, device)

    if args.seed is not None:
        torch.manual_seed(args.seed)
        np.random.seed(args.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(args.seed)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    vl_chat_processor = VLChatProcessor.from_pretrained(args.model_id)
    tokenizer = vl_chat_processor.tokenizer
    vl_gpt = MultiModalityCausalLM.from_pretrained(args.model_id, trust_remote_code=True)
    vl_gpt = vl_gpt.to(dtype=dtype)
    if device == "cuda":
        vl_gpt = vl_gpt.cuda().eval()
    else:
        vl_gpt = vl_gpt.to(device).eval()

    vae = AutoencoderKL.from_pretrained("stabilityai/sdxl-vae")
    vae = vae.to(dtype=dtype)
    if device == "cuda":
        vae = vae.cuda().eval()
    else:
        vae = vae.to(device).eval()

    messages = [{"role": "User", "content": args.prompt}, {"role": "Assistant", "content": ""}]
    sft_format = vl_chat_processor.apply_sft_template_for_multi_turn_prompts(
        conversations=messages,
        sft_format=vl_chat_processor.sft_format,
        system_prompt="",
    )
    prompt = sft_format + vl_chat_processor.image_gen_tag
    input_ids = torch.LongTensor(tokenizer.encode(prompt)).to(device)

    tokens = torch.stack([input_ids] * (2 * args.batch_size)).to(device)
    tokens[args.batch_size :, 1:] = vl_chat_processor.pad_id
    inputs_embeds = vl_gpt.language_model.get_input_embeddings()(tokens)
    inputs_embeds = inputs_embeds[:, :-1, :]

    z = torch.randn((args.batch_size, 4, 48, 48), dtype=dtype, device=device)
    dt = torch.zeros_like(z) + (1.0 / args.num_inference_steps)
    attention_mask = torch.ones((2 * args.batch_size, inputs_embeds.shape[1] + 577), device=device).int()
    attention_mask[args.batch_size :, 1 : inputs_embeds.shape[1]] = 0

    past_key_values = None
    with torch.inference_mode():
        for step in range(args.num_inference_steps):
            z_input = torch.cat([z, z], dim=0)
            t = torch.full((z_input.shape[0],), float(step) / args.num_inference_steps * 1000.0, device=device, dtype=torch.float32)
            z_enc = vl_gpt.vision_gen_enc_model(z_input, t)
            z_emb, t_emb, hs = z_enc[0], z_enc[1], z_enc[2]
            z_emb = z_emb.view(z_emb.shape[0], z_emb.shape[1], -1).permute(0, 2, 1)
            z_emb = vl_gpt.vision_gen_enc_aligner(z_emb)
            llm_emb = torch.cat([inputs_embeds, t_emb.unsqueeze(1), z_emb], dim=1)

            outputs = vl_gpt.language_model.model(
                inputs_embeds=llm_emb,
                use_cache=True,
                attention_mask=attention_mask,
                past_key_values=past_key_values,
            )
            past_key_values = outputs.past_key_values
            hidden_states = outputs.last_hidden_state
            hidden_states = vl_gpt.vision_gen_dec_aligner(
                vl_gpt.vision_gen_dec_aligner_norm(hidden_states[:, -576:, :])
            )
            hidden_states = hidden_states.reshape(z_emb.shape[0], 24, 24, 768).permute(0, 3, 1, 2)
            v = vl_gpt.vision_gen_dec_model(hidden_states, hs, t_emb)
            v_cond, v_uncond = torch.chunk(v, 2)
            v = args.cfg_weight * v_cond - (args.cfg_weight - 1.0) * v_uncond
            z = z + dt * v

        decoded_image = vae.decode(z / vae.config.scaling_factor).sample

    images = decoded_image.float().clip_(-1.0, 1.0).permute(0, 2, 3, 1).cpu().numpy()
    images = ((images + 1) / 2.0 * 255).astype(np.uint8)

    for idx in range(images.shape[0]):
        path = output_dir / f"janusflow_{idx:02d}.png"
        PIL.Image.fromarray(images[idx]).resize((1024, 1024), PIL.Image.LANCZOS).save(path)
        print(path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dry-run or execute JanusFlow rectified-flow image generation.")
    parser.add_argument("--model-id", default="deepseek-ai/JanusFlow-1.3B", help="Hugging Face model id.")
    parser.add_argument("--prompt", required=True, help="Text prompt to generate from.")
    parser.add_argument("--output-dir", default="generated_samples", help="Directory for generated images.")
    parser.add_argument("--cfg-weight", type=float, default=2.0, help="Classifier-free guidance weight.")
    parser.add_argument("--num-inference-steps", type=int, default=30, help="Number of rectified-flow steps.")
    parser.add_argument("--batch-size", type=int, default=5, help="Number of images to generate in parallel.")
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
