#!/usr/bin/env python3
"""Suggest conservative vLLM serving flags for memory-oriented deployments.

The planner is intentionally heuristic. It does not inspect or download a model
and cannot prove that a deployment will fit. Use its output as a checklist and
starting command, then validate with vLLM startup logs and a smoke request.
"""

from __future__ import annotations

import argparse
import shlex
from typing import Iterable


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def non_negative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def add_flag(command: list[str], flag: str, value: object | None = None) -> None:
    command.append(flag)
    if value is not None:
        command.append(str(value))


def shell_join(command: Iterable[str]) -> str:
    return " \\\n  ".join(shlex.quote(part) for part in command)


def build_command(args: argparse.Namespace) -> list[str]:
    command = ["vllm", "serve", args.model]
    add_flag(command, "--tensor-parallel-size", args.tensor_parallel_size)
    if args.pipeline_parallel_size > 1:
        add_flag(command, "--pipeline-parallel-size", args.pipeline_parallel_size)
    if args.data_parallel_size > 1:
        add_flag(command, "--data-parallel-size", args.data_parallel_size)
    if args.max_model_len:
        add_flag(command, "--max-model-len", args.max_model_len)
    if args.max_num_seqs:
        add_flag(command, "--max-num-seqs", args.max_num_seqs)
    add_flag(command, "--gpu-memory-utilization", args.gpu_memory_utilization)
    if args.cpu_offload_gb > 0:
        add_flag(command, "--cpu-offload-gb", args.cpu_offload_gb)
    if args.kv_cache_memory_bytes:
        add_flag(command, "--kv-cache-memory-bytes", args.kv_cache_memory_bytes)
    if args.quantization:
        add_flag(command, "--quantization", args.quantization)
    add_flag(command, "--dtype", args.dtype)
    if args.enforce_eager:
        add_flag(command, "--enforce-eager")
    if args.distributed_executor_backend:
        add_flag(
            command,
            "--distributed-executor-backend",
            args.distributed_executor_backend,
        )
    if args.enable_prefix_caching:
        add_flag(command, "--enable-prefix-caching")
    return command


def recommendations(args: argparse.Namespace) -> list[str]:
    total_model_parallel = args.tensor_parallel_size * args.pipeline_parallel_size
    required_gpus = total_model_parallel * args.data_parallel_size
    notes = [
        f"Estimated GPUs required: {required_gpus} "
        f"(TP {args.tensor_parallel_size} × PP {args.pipeline_parallel_size} "
        f"× DP {args.data_parallel_size}).",
    ]
    if required_gpus > args.num_gpus:
        notes.append(
            "WARNING: requested parallelism needs more GPUs than --num-gpus; "
            "reduce TP/PP/DP or provision more GPUs."
        )
    if args.tensor_parallel_size > args.num_gpus:
        notes.append("WARNING: tensor parallel size exceeds available GPUs.")
    if args.num_gpus > 1 and args.tensor_parallel_size == 1:
        notes.append(
            "If the model OOMs on one GPU, increase --tensor-parallel-size "
            "before adding CPU offload."
        )
    if args.pipeline_parallel_size > 1:
        notes.append(
            "Pipeline parallelism is useful across nodes or uneven GPU splits; "
            "validate model PP support and layer balance."
        )
    if args.data_parallel_size > 1:
        notes.append(
            "Data parallel ranks have independent KV caches; --max-num-seqs "
            "applies per rank and load balancing affects prefix-cache locality."
        )
    if args.max_model_len is None:
        notes.append(
            "Set --max-model-len to the application requirement if startup logs "
            "show low KV cache capacity or OOM."
        )
    elif args.max_model_len > 32768:
        notes.append(
            "Long context strongly increases KV pressure; inspect startup "
            "Maximum concurrency and consider TP/DCP/offload."
        )
    if args.gpu_memory_utilization > 0.92:
        notes.append(
            "High GPU memory utilization can improve KV capacity but may leave "
            "too little headroom for kernels, fragmentation, or colocated services."
        )
    if args.gpu_memory_utilization < 0.80:
        notes.append(
            "Low GPU memory utilization is safer for shared GPUs but reduces KV "
            "capacity and maximum concurrency."
        )
    if args.cpu_offload_gb > 0:
        notes.append(
            "CPU weight offload trades GPU memory for host memory and transfer "
            "latency; verify PCIe/NVLink bandwidth and latency SLOs."
        )
    if args.kv_cache_memory_bytes:
        notes.append(
            "Explicit KV cache bytes override automatic sizing from "
            "--gpu-memory-utilization; validate startup cache logs carefully."
        )
    if args.quantization:
        notes.append(
            "Quantization support is platform and model dependent; verify startup "
            "logs and output quality on representative prompts."
        )
    if args.enforce_eager:
        notes.append(
            "--enforce-eager is helpful for CUDA graph debugging and memory "
            "reduction but can reduce throughput."
        )
    notes.extend(
        [
            "After launch, check startup logs for GPU KV cache size and maximum concurrency.",
            "Then run one smoke request before any benchmark.",
            "For production measurements, compare TTFT, TPOT/ITL, queue length, KV cache usage, and GPU utilization.",
        ]
    )
    return notes


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print a conservative vLLM serve command and memory checklist."
    )
    parser.add_argument("--model", required=True, help="Model ID or path placeholder.")
    parser.add_argument(
        "--num-gpus",
        type=positive_int,
        default=1,
        help="GPUs available for this deployment. Default: 1.",
    )
    parser.add_argument(
        "--tensor-parallel-size",
        type=positive_int,
        default=1,
        help="Tensor parallel size. Default: 1.",
    )
    parser.add_argument(
        "--pipeline-parallel-size",
        type=positive_int,
        default=1,
        help="Pipeline parallel size. Default: 1.",
    )
    parser.add_argument(
        "--data-parallel-size",
        type=positive_int,
        default=1,
        help="Data parallel size. Default: 1.",
    )
    parser.add_argument("--max-model-len", type=positive_int)
    parser.add_argument("--max-num-seqs", type=positive_int)
    parser.add_argument(
        "--gpu-memory-utilization",
        type=float,
        default=0.90,
        help="Suggested per-instance GPU memory fraction. Default: 0.90.",
    )
    parser.add_argument(
        "--cpu-offload-gb",
        type=non_negative_float,
        default=0.0,
        help="Weight offload budget in GiB. Default: 0.",
    )
    parser.add_argument("--kv-cache-memory-bytes", type=positive_int)
    parser.add_argument("--quantization")
    parser.add_argument(
        "--dtype",
        default="auto",
        choices=("auto", "float16", "bfloat16", "float32"),
        help="Model dtype flag to include in the suggested command. Default: auto.",
    )
    parser.add_argument(
        "--distributed-executor-backend",
        choices=("mp", "ray", "uni", "external_launcher"),
    )
    parser.add_argument("--enable-prefix-caching", action="store_true")
    parser.add_argument("--enforce-eager", action="store_true")
    args = parser.parse_args()

    if not 0 < args.gpu_memory_utilization <= 1:
        parser.error("--gpu-memory-utilization must be in (0, 1].")

    print("Suggested command")
    print("=================")
    print(shell_join(build_command(args)))
    print("\nChecklist")
    print("=========")
    for note in recommendations(args):
        print(f"- {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
