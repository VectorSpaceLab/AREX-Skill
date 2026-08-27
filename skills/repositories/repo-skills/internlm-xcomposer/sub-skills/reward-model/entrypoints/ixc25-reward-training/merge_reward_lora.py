#!/usr/bin/env python3
"""Merge an IXC-2.5-Reward LoRA adapter into a standalone model directory."""
from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge IXC-2.5-Reward PEFT LoRA adapter into a base reward model")
    parser.add_argument("--adapter-model-name", required=True, help="Path to the trained reward LoRA adapter directory.")
    parser.add_argument("--base-model-name", default="internlm/internlm-xcomposer2d5-7b-reward", help="Base reward model id or local checkpoint path.")
    parser.add_argument("--output-name", required=True, help="Output directory for the merged reward model.")
    parser.add_argument("--device-map", default="cuda", help="Transformers device_map for loading the base model. Default: cuda.")
    parser.add_argument("--torch-dtype", choices=("fp16", "bf16", "fp32"), default="fp16")
    args = parser.parse_args()

    import torch
    from peft import PeftModel
    from transformers import AutoModel, AutoTokenizer

    dtype = torch.float16 if args.torch_dtype == "fp16" else torch.bfloat16 if args.torch_dtype == "bf16" else torch.float32
    model = AutoModel.from_pretrained(
        args.base_model_name,
        device_map=args.device_map,
        torch_dtype=dtype,
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(args.base_model_name, trust_remote_code=True)
    model.tokenizer = tokenizer
    model = PeftModel.from_pretrained(model, args.adapter_model_name)
    model = model.merge_and_unload()
    model.save_pretrained(args.output_name)
    tokenizer.save_pretrained(args.output_name)
    print(f"merged reward LoRA adapter into {args.output_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
