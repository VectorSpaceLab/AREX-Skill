#!/usr/bin/env python3
"""Merge OmniLive base/adapter components into merge_lora/."""
from __future__ import annotations

import argparse
import os


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge OmniLive base and adapter components with PEFT")
    parser.add_argument("--model-root", default=os.environ.get("IXC_OMNILIVE_MODEL_ROOT", "internlm-xcomposer2d5-ol-7b"))
    parser.add_argument("--base-dir", default="", help="Defaults to <model-root>/base")
    parser.add_argument("--adapter-dir", default="", help="Defaults to <model-root>/adapter")
    parser.add_argument("--output-dir", default="", help="Defaults to <model-root>/merge_lora")
    parser.add_argument("--torch-dtype", choices=["bf16", "fp16", "fp32"], default="bf16")
    args = parser.parse_args()

    import torch
    from peft import PeftConfig, PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    base_dir = args.base_dir or os.path.join(args.model_root, "base")
    adapter_dir = args.adapter_dir or os.path.join(args.model_root, "adapter")
    output_dir = args.output_dir or os.path.join(args.model_root, "merge_lora")
    dtype = torch.bfloat16 if args.torch_dtype == "bf16" else torch.float16 if args.torch_dtype == "fp16" else torch.float32

    PeftConfig.from_pretrained(adapter_dir)
    model = AutoModelForCausalLM.from_pretrained(base_dir, return_dict=True, torch_dtype=dtype, trust_remote_code=True)
    tokenizer = AutoTokenizer.from_pretrained(base_dir, trust_remote_code=True)
    model = PeftModel.from_pretrained(model, adapter_dir)
    model.eval()
    model = model.merge_and_unload()
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"merged OmniLive LoRA adapter into {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
