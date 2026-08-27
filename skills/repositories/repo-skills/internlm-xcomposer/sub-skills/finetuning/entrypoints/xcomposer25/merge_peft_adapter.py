#!/usr/bin/env python3
"""Merge an InternLM-XComposer2.5 PEFT LoRA adapter into a standalone model directory."""
from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Merge an InternLM-XComposer2.5 PEFT adapter with its base model."
    )
    parser.add_argument(
        "--adapter_model_name",
        "--adapter-model-name",
        dest="adapter_model_name",
        required=True,
        help="Path to the trained PEFT adapter directory.",
    )
    parser.add_argument(
        "--base_model_name",
        "--base-model-name",
        dest="base_model_name",
        required=True,
        help="Base InternLM-XComposer2.5 model id or local checkpoint directory.",
    )
    parser.add_argument(
        "--output_name",
        "--output-name",
        dest="output_name",
        required=True,
        help="Output directory for the merged standalone checkpoint.",
    )
    parser.add_argument(
        "--torch-dtype",
        choices=("bf16", "fp16", "fp32"),
        default="bf16",
        help="Dtype used when loading the base model. Default: bf16, matching the source merge script.",
    )
    parser.add_argument(
        "--device-map",
        default=None,
        help="Optional Transformers device_map for loading the base model, e.g. cuda:0 or auto.",
    )
    args = parser.parse_args()

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    dtype = {
        "bf16": torch.bfloat16,
        "fp16": torch.float16,
        "fp32": torch.float32,
    }[args.torch_dtype]
    load_kwargs = {
        "return_dict": True,
        "torch_dtype": dtype,
        "trust_remote_code": True,
    }
    if args.device_map:
        load_kwargs["device_map"] = args.device_map

    model = AutoModelForCausalLM.from_pretrained(args.base_model_name, **load_kwargs)
    tokenizer = AutoTokenizer.from_pretrained(args.base_model_name, trust_remote_code=True)
    model = PeftModel.from_pretrained(model, args.adapter_model_name).eval()
    model = model.merge_and_unload()
    model.save_pretrained(args.output_name)
    tokenizer.save_pretrained(args.output_name)
    print(f"merged PEFT adapter into {args.output_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
