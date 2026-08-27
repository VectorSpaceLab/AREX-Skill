#!/usr/bin/env python3
"""Dry-run requirement/resource checklist for Fengshen example families.

This script prints planning guidance only. It never installs packages, downloads
models or datasets, launches training, or mutates checkpoints.
"""
from __future__ import annotations

import argparse

RECIPES = {
    "taiyi-inference": {
        "deps": ["torch", "transformers", "diffusers", "accelerate (optional for fp16/cuda)"],
        "data": "prompt text plus authorized Hugging Face/local model cache",
        "notes": ["fp32/full precision can be planned for CPU or CUDA but may be slow/heavy", "fp16 path requires CUDA and compatible model weights"],
    },
    "taiyi-finetune": {
        "deps": ["diffusers", "accelerate", "deepspeed or optimizer variant as selected"],
        "data": "captioned image dataset and output checkpoint directory",
        "notes": ["resource-heavy; examples cite high VRAM/RAM", "do not overwrite source model directory"],
    },
    "ziya-inference": {
        "deps": ["transformers", "accelerate", "bitsandbytes or llama.cpp variant if quantized"],
        "data": "Ziya/LLaMA checkpoint, tokenizer, prompt file or interactive prompt",
        "notes": ["large model; verify RAM/VRAM", "quantization backend changes dependency stack"],
    },
    "classification": {
        "deps": ["torch", "transformers", "datasets", "pytorch-lightning", "fengshen"],
        "data": "classification JSON/JSONL or Hugging Face dataset with sentence/sentence2/label fields",
        "notes": ["use pipelines-cli fixture helpers before training", "Deepspeed scripts require backend planning"],
    },
    "clue": {
        "deps": ["torch", "transformers", "datasets", "fengshen"],
        "data": "downloaded CLUE task files plus submission conversion outputs",
        "notes": ["leaderboard scripts are not safe default verification", "confirm task-specific labels and submission format"],
    },
    "nlg-nlt": {
        "deps": ["torch", "transformers", "sentencepiece when tokenizer requires it", "fengshen"],
        "data": "source/target pairs for summary, QA, question generation, translation, or reasoning",
        "notes": ["validate source and target max lengths separately", "model downloads are outside dry-run scope"],
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a non-mutating Fengshen recipe requirement checklist.")
    parser.add_argument("--recipe", choices=sorted(RECIPES), required=True)
    parser.add_argument("--device", choices=["cpu", "cuda", "multi-gpu", "unknown"], default="unknown")
    parser.add_argument("--precision", choices=["fp32", "fp16", "bf16", "int8", "int4", "unknown"], default="unknown")
    parser.add_argument("--gpus", type=int, default=0)
    parser.add_argument("--vram-gb", type=float, default=0.0)
    args = parser.parse_args()

    r = RECIPES[args.recipe]
    print(f"recipe: {args.recipe}")
    print(f"requested device: {args.device}; precision: {args.precision}; gpus: {args.gpus}; vram_gb: {args.vram_gb}")
    print("dependencies to verify (not installed by this script):")
    for dep in r["deps"]:
        print(f"- {dep}")
    print(f"data/checkpoint inputs to collect: {r['data']}")
    print("notes:")
    for note in r["notes"]:
        print(f"- {note}")
    if args.precision == "fp16" and args.device == "cpu":
        print("WARNING: fp16 CPU is not a suitable substitute for the CUDA fp16 examples.")
    if args.device in {"cuda", "multi-gpu"} and args.gpus <= 0:
        print("WARNING: CUDA/multi-GPU recipe requested but --gpus was not set.")
    print("dry_run: no installs, downloads, training, services, or checkpoint writes performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
