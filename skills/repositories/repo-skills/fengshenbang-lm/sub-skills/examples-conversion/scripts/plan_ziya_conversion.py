#!/usr/bin/env python3
"""Dry-run Ziya/Fengshen LLaMA conversion planner.

This script prints a checklist only. It never reads checkpoint tensors, writes
outputs, invokes conversion utilities, or mutates model directories.
"""
from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan Ziya/LLaMA HF/Fengshen/tensor-parallel conversion safely.")
    parser.add_argument("--source-format", choices=["hf", "fengshen", "fengshen-tp", "llama-cpp", "unknown"], required=True)
    parser.add_argument("--target", choices=["hf-inference", "fs-finetune", "fs-tp", "llama-cpp-quant", "merge-to-hf"], required=True)
    parser.add_argument("--model-size", default="unknown", help="Example: 7b, 13b, 65b, unknown.")
    parser.add_argument("--gpus", type=int, default=0)
    parser.add_argument("--vram-gb", type=float, default=0.0)
    parser.add_argument("--tensor-parallel", type=int, default=1)
    parser.add_argument("--allow-mutation", action="store_true", help="Acknowledge that a future real conversion would write large outputs. This script still does not mutate.")
    args = parser.parse_args()

    print("Ziya/LLaMA conversion dry-run plan")
    print(f"source_format: {args.source_format}")
    print(f"target: {args.target}")
    print(f"model_size: {args.model_size}")
    print(f"gpus: {args.gpus}; vram_gb_per_gpu: {args.vram_gb}; tensor_parallel: {args.tensor_parallel}")
    print("\ninputs to collect before a real conversion:")
    print("- source checkpoint directory and tokenizer files")
    print("- empty output directory distinct from the source")
    print("- exact Fengshen/Transformers dependency stack")
    print("- expected tensor-parallel degree and shard naming")
    print("- backup/rollback plan for large outputs")

    print("\nlikely utility family:")
    if args.target == "fs-tp" or args.target == "fs-finetune":
        print("- HF/Fengshen conversion helpers and tensor-parallel split scripts from the Fengshen LLaMA utilities")
    elif args.target == "merge-to-hf":
        print("- merge Fengshen/tensor-parallel weights back toward Hugging Face layout")
    elif args.target == "llama-cpp-quant":
        print("- external llama.cpp quantization path; verify its separate build/runtime requirements")
    else:
        print("- no conversion may be needed; prefer direct Hugging Face inference if memory allows")

    print("\nresource warnings:")
    if args.target in {"fs-finetune", "fs-tp"} and args.gpus == 0:
        print("- WARNING: Fengshen Ziya fine-tuning/conversion examples assume GPU resources; provide --gpus for planning.")
    if args.tensor_parallel > 1 and args.gpus and args.tensor_parallel > args.gpus:
        print("- WARNING: tensor parallel degree exceeds GPU count.")
    if not args.allow_mutation:
        print("- A real conversion is mutating. Re-run planning with explicit user approval and a safe output directory before converting.")
    print("\ndry_run: no checkpoint files read or written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
