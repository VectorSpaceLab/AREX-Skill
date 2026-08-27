#!/usr/bin/env python3
"""Run OmniLive base VLM image chat from a local model root."""
from __future__ import annotations

import argparse
import os


def auto_configure_device_map(num_gpus: int):
    num_trans_layers = 32
    per_gpu_layers = 38 / num_gpus
    device_map = {
        'vit': 0,
        'vision_proj': 0,
        'model.tok_embeddings': 0,
        'plora_glb_GN': 0,
        'plora_sub_GN': 0,
        'model.norm': num_gpus - 1,
        'output': num_gpus - 1,
    }
    used = 3
    gpu_target = 0
    for i in range(num_trans_layers):
        if used >= per_gpu_layers:
            gpu_target += 1
            used = 0
        assert gpu_target < num_gpus
        device_map[f'model.layers.{i}'] = gpu_target
        used += 1
    return device_map


def main() -> int:
    parser = argparse.ArgumentParser(description="OmniLive base VLM image chat entrypoint")
    parser.add_argument("--model-root", default=os.environ.get("IXC_OMNILIVE_MODEL_ROOT", "internlm-xcomposer2d5-ol-7b"))
    parser.add_argument("--base-model-path", default="", help="Override base component path. Defaults to <model-root>/base.")
    parser.add_argument("--image", action="append", required=True, help="Image path. Repeat for multi-image prompts.")
    parser.add_argument("--question", default="Analyze the given image in a detailed manner")
    parser.add_argument("--num-gpus", default=1, type=int)
    parser.add_argument("--dtype", choices=["fp16", "bf16", "fp32"], default="fp16")
    parser.add_argument("--num-beams", type=int, default=3)
    parser.add_argument("--use-meta", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    import torch
    from transformers import AutoModel, AutoTokenizer

    torch.set_grad_enabled(False)
    model_path = args.base_model_path or os.path.join(args.model_root, "base")
    torch_dtype = torch.bfloat16 if args.dtype == "bf16" else torch.float16 if args.dtype == "fp16" else torch.float32
    model = AutoModel.from_pretrained(model_path, torch_dtype=torch_dtype, trust_remote_code=True).eval().cuda()
    if args.dtype == "fp16":
        model = model.half()
    if args.num_gpus > 1:
        from accelerate import dispatch_model
        model = dispatch_model(model, device_map=auto_configure_device_map(args.num_gpus))
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model.tokenizer = tokenizer
    with torch.autocast(device_type='cuda', dtype=torch.float16):
        response, _ = model.chat(tokenizer, args.question, args.image, do_sample=False, num_beams=args.num_beams, use_meta=args.use_meta)
    print(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
