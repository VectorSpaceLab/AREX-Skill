#!/usr/bin/env python3
"""Bounded nano-vLLM throughput benchmark helper.

Full execution requires CUDA and local Qwen3 weights. Use --dry-run to validate
workload size and configuration without importing nano-vLLM or loading weights.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import time
from pathlib import Path


def validate_model_dir(path: str) -> Path:
    model_dir = Path(os.path.expanduser(path)).resolve()
    if not model_dir.is_dir():
        raise SystemExit(f"model directory does not exist: {path}")
    if not (model_dir / "config.json").exists():
        raise SystemExit(f"missing config.json in model directory: {model_dir}")
    if not any(model_dir.glob("*.safetensors")):
        raise SystemExit(f"no .safetensors files found in model directory: {model_dir}")
    return model_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a nano-vLLM random-token throughput benchmark.")
    parser.add_argument("--model", required=True, help="Local Qwen3-format model directory.")
    parser.add_argument("--num-seqs", type=int, default=256, help="Number of benchmark requests.")
    parser.add_argument("--min-input-len", type=int, default=100)
    parser.add_argument("--max-input-len", type=int, default=1024)
    parser.add_argument("--min-output-len", type=int, default=100)
    parser.add_argument("--max-output-len", type=int, default=1024)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--warmup-prompt", default="Benchmark: ")
    parser.add_argument("--tensor-parallel-size", type=int, default=1)
    parser.add_argument("--max-model-len", type=int, default=4096)
    parser.add_argument("--max-num-batched-tokens", type=int, default=16384)
    parser.add_argument("--max-num-seqs", type=int, default=512)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.9)
    parser.add_argument("--kvcache-block-size", type=int, default=256)
    parser.add_argument("--enforce-eager", action="store_true", help="Disable CUDA graph capture.")
    eos = parser.add_mutually_exclusive_group()
    eos.add_argument("--ignore-eos", dest="ignore_eos", action="store_true", default=True, help="Fixed-token throughput mode (default).")
    eos.add_argument("--respect-eos", dest="ignore_eos", action="store_false", help="Allow EOS to stop requests early.")
    parser.add_argument("--dry-run", action="store_true", help="Validate args and print workload summary without constructing LLM.")
    parser.add_argument("--json", action="store_true", help="Emit a JSON summary after a full run or dry run.")
    return parser


def validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.num_seqs <= 0:
        parser.error("--num-seqs must be positive")
    if not (0 < args.min_input_len <= args.max_input_len):
        parser.error("input length range must be positive and ordered")
    if not (0 < args.min_output_len <= args.max_output_len):
        parser.error("output length range must be positive and ordered")
    if args.max_model_len <= 0:
        parser.error("--max-model-len must be positive")
    if args.max_num_batched_tokens <= 0 or args.max_num_seqs <= 0:
        parser.error("scheduler limits must be positive")
    if not (1 <= args.tensor_parallel_size <= 8):
        parser.error("--tensor-parallel-size must be between 1 and 8")
    if args.kvcache_block_size % 256 != 0:
        parser.error("--kvcache-block-size must be a multiple of 256")
    if not (0 < args.gpu_memory_utilization <= 1):
        parser.error("--gpu-memory-utilization must be in (0, 1]")


def make_workload(args: argparse.Namespace) -> tuple[list[list[int]], list[int]]:
    rng = random.Random(args.seed)
    prompt_token_ids = [
        [rng.randint(0, 10000) for _ in range(rng.randint(args.min_input_len, args.max_input_len))]
        for _ in range(args.num_seqs)
    ]
    output_lengths = [rng.randint(args.min_output_len, args.max_output_len) for _ in range(args.num_seqs)]
    return prompt_token_ids, output_lengths


def summary(args: argparse.Namespace, model_dir: Path, output_lengths: list[int]) -> dict[str, object]:
    return {
        "model": str(model_dir),
        "num_seqs": args.num_seqs,
        "input_len_range": [args.min_input_len, args.max_input_len],
        "output_len_range": [args.min_output_len, args.max_output_len],
        "requested_output_tokens": sum(output_lengths),
        "seed": args.seed,
        "ignore_eos": args.ignore_eos,
        "config": {
            "tensor_parallel_size": args.tensor_parallel_size,
            "max_model_len": args.max_model_len,
            "max_num_batched_tokens": args.max_num_batched_tokens,
            "max_num_seqs": args.max_num_seqs,
            "gpu_memory_utilization": args.gpu_memory_utilization,
            "kvcache_block_size": args.kvcache_block_size,
            "enforce_eager": args.enforce_eager,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(parser, args)
    model_dir = validate_model_dir(args.model)
    prompt_token_ids, output_lengths = make_workload(args)
    run_summary = summary(args, model_dir, output_lengths)

    if args.dry_run:
        print(json.dumps(run_summary, indent=2) if args.json else run_summary)
        return 0

    from nanovllm import LLM, SamplingParams

    llm = LLM(
        str(model_dir),
        enforce_eager=args.enforce_eager,
        tensor_parallel_size=args.tensor_parallel_size,
        max_model_len=args.max_model_len,
        max_num_batched_tokens=args.max_num_batched_tokens,
        max_num_seqs=args.max_num_seqs,
        gpu_memory_utilization=args.gpu_memory_utilization,
        kvcache_block_size=args.kvcache_block_size,
    )
    try:
        sampling_params = [
            SamplingParams(temperature=0.6, ignore_eos=args.ignore_eos, max_tokens=length)
            for length in output_lengths
        ]
        llm.generate([args.warmup_prompt], SamplingParams(max_tokens=1), use_tqdm=False)
        start = time.time()
        llm.generate(prompt_token_ids, sampling_params, use_tqdm=False)
        elapsed = time.time() - start
    finally:
        llm.exit()

    total_tokens = sum(output_lengths)
    throughput = total_tokens / elapsed if elapsed > 0 else float("inf")
    run_summary.update({"elapsed_seconds": elapsed, "throughput_tokens_per_second": throughput})
    if args.json:
        print(json.dumps(run_summary, indent=2))
    else:
        print(f"Total: {total_tokens}tok, Time: {elapsed:.2f}s, Throughput: {throughput:.2f}tok/s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
