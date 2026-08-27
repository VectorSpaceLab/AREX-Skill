#!/usr/bin/env python3
"""Extract the LLaVA language model and tokenizer for HunyuanVideo text_encoder/.

This is a self-contained adaptation of HunyuanVideo's preprocessing utility. It
expects an already-downloaded local LLaVA Transformers directory and writes the
language-model/tokenizer files that HunyuanVideo expects under text_encoder/.
It performs no network download.

Example:
  python extract_llava_text_encoder.py --input-dir ckpts/llava-llama-3-8b-v1_1-transformers --output-dir ckpts/text_encoder
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract LLaVA language model/tokenizer for HunyuanVideo text_encoder.")
    parser.add_argument("--input-dir", required=True, help="Local xtuner/llava-llama-3-8b-v1_1-transformers directory.")
    parser.add_argument("--output-dir", required=True, help="Output directory for HunyuanVideo text_encoder files.")
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"], help="Device for loading the source model; auto prefers CUDA when available.")
    parser.add_argument("--dtype", default="fp16", choices=["fp16", "bf16", "fp32"], help="Torch dtype for loading the source model.")
    args = parser.parse_args()

    input_dir = Path(args.input_dir).expanduser()
    output_dir = Path(args.output_dir).expanduser()
    if not input_dir.exists():
        raise SystemExit(f"Input directory does not exist: {input_dir}")

    import torch
    from transformers import AutoProcessor, LlavaForConditionalGeneration

    dtype_map = {"fp16": torch.float16, "bf16": torch.bfloat16, "fp32": torch.float32}
    if args.device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device

    processor = AutoProcessor.from_pretrained(str(input_dir))
    model = LlavaForConditionalGeneration.from_pretrained(
        str(input_dir),
        torch_dtype=dtype_map[args.dtype],
        low_cpu_mem_usage=True,
    ).to(device)

    output_dir.mkdir(parents=True, exist_ok=True)
    model.language_model.save_pretrained(str(output_dir))
    processor.tokenizer.save_pretrained(str(output_dir))
    print(f"Saved HunyuanVideo text_encoder files to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
