#!/usr/bin/env python3
"""Parameterized nano-vLLM offline generation wrapper.

This adapts the package's basic generation pattern into a reusable CLI. Full
execution requires a CUDA-capable nano-vLLM environment and a local Qwen3 model
directory; --help and argument validation do not load weights.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable


def read_prompt_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    blocks = [block.strip() for block in text.split("\n\n") if block.strip()]
    return blocks or ([text.strip()] if text.strip() else [])


def collect_prompts(values: Iterable[str] | None, prompt_file: str | None) -> list[str]:
    prompts = list(values or [])
    if prompt_file:
        prompts.extend(read_prompt_file(Path(prompt_file)))
    return prompts


def validate_model_dir(path: str, require_tokenizer: bool) -> Path:
    model_dir = Path(os.path.expanduser(path)).resolve()
    if not model_dir.is_dir():
        raise SystemExit(f"model directory does not exist: {path}")
    if not (model_dir / "config.json").exists():
        raise SystemExit(f"missing config.json in model directory: {model_dir}")
    if not any(model_dir.glob("*.safetensors")):
        raise SystemExit(f"no .safetensors files found in model directory: {model_dir}")
    if require_tokenizer and not any(model_dir.glob("tokenizer*")) and not any(model_dir.glob("*vocab*")) and not any(model_dir.glob("*merges*")):
        raise SystemExit(f"no tokenizer files found in model directory: {model_dir}")
    return model_dir


def apply_chat_template(model_dir: Path, prompts: list[str], system_prompt: str | None) -> list[str]:
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(str(model_dir), use_fast=True)
    rendered = []
    for prompt in prompts:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        rendered.append(tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True))
    return rendered


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run nano-vLLM generation against a local Qwen3 model directory.")
    parser.add_argument("--model", required=True, help="Local Hugging Face Qwen3-format model directory.")
    parser.add_argument("--prompt", action="append", help="Prompt text. Repeat for multiple prompts.")
    parser.add_argument("--prompt-file", help="UTF-8 text file; blank lines separate multiple prompts.")
    parser.add_argument("--system-prompt", help="Optional system message used when applying a chat template.")
    parser.add_argument("--no-chat-template", action="store_true", help="Send prompt strings directly without tokenizer.apply_chat_template.")
    parser.add_argument("--temperature", type=float, default=0.6, help="Positive sampling temperature; zero/greedy is not supported.")
    parser.add_argument("--max-tokens", type=int, default=128, help="Maximum completion tokens per prompt.")
    parser.add_argument("--ignore-eos", action="store_true", help="Continue generation until max tokens even if EOS is sampled.")
    parser.add_argument("--tensor-parallel-size", type=int, default=1, help="Number of tensor-parallel GPU ranks.")
    parser.add_argument("--max-model-len", type=int, default=4096, help="Requested maximum model/context length.")
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.9, help="Fraction of GPU memory used for KV cache sizing.")
    parser.add_argument("--enforce-eager", action="store_true", help="Disable CUDA graph capture; recommended for first smoke tests.")
    parser.add_argument("--use-tqdm", action="store_true", help="Show nano-vLLM progress bar.")
    parser.add_argument("--json", action="store_true", help="Emit JSON records instead of text blocks.")
    parser.add_argument("--dry-run", action="store_true", help="Validate arguments and show rendered prompt count without loading LLM weights.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.temperature <= 1e-10:
        parser.error("--temperature must be > 1e-10; nano-vLLM rejects greedy zero temperature")
    if args.max_tokens <= 0:
        parser.error("--max-tokens must be positive")
    if not (1 <= args.tensor_parallel_size <= 8):
        parser.error("--tensor-parallel-size must be between 1 and 8")
    if not (0 < args.gpu_memory_utilization <= 1):
        parser.error("--gpu-memory-utilization must be in (0, 1]")

    model_dir = validate_model_dir(args.model, require_tokenizer=not args.no_chat_template)
    prompts = collect_prompts(args.prompt, args.prompt_file)
    if not prompts:
        parser.error("provide at least one --prompt or --prompt-file")

    rendered = prompts if args.no_chat_template else apply_chat_template(model_dir, prompts, args.system_prompt)
    if args.dry_run:
        print(json.dumps({"model": str(model_dir), "prompts": len(rendered), "chat_template": not args.no_chat_template}, indent=2))
        return 0

    from nanovllm import LLM, SamplingParams

    llm = LLM(
        str(model_dir),
        enforce_eager=args.enforce_eager,
        tensor_parallel_size=args.tensor_parallel_size,
        max_model_len=args.max_model_len,
        gpu_memory_utilization=args.gpu_memory_utilization,
    )
    try:
        sampling = SamplingParams(temperature=args.temperature, max_tokens=args.max_tokens, ignore_eos=args.ignore_eos)
        outputs = llm.generate(rendered, sampling, use_tqdm=args.use_tqdm)
    finally:
        llm.exit()

    if args.json:
        print(json.dumps(outputs, ensure_ascii=False, indent=2))
    else:
        for idx, (prompt, output) in enumerate(zip(prompts, outputs)):
            print(f"=== completion {idx} ===")
            print(f"prompt: {prompt}")
            print(output["text"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
