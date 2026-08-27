#!/usr/bin/env python3
"""Plan rough vLLM-Omni stage placement and gpu_memory_utilization values.

This is a no-model-loading helper derived from vLLM-Omni's stage memory planning
logic. It uses only user-provided GPU memory and stage names, so it is safe to
run before downloading model weights. Treat the output as a starting point; real
serving should still monitor peak memory and adjust per model.

Examples:
    python scripts/plan_stage_memory.py --num-gpus 2 --gpu-mem-gib 80 --stages thinker,talker,code2wav
    python scripts/plan_stage_memory.py --gpu-mem-gib 40,40,40 --stages ar,dit,vae --headroom-gib 4 --streaming
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass


@dataclass
class StagePlan:
    stage_id: int
    name: str
    device: str
    gpu_memory_utilization: float
    max_num_seqs_hint: int
    enforce_eager_hint: bool
    async_scheduling_hint: bool
    notes: list[str]


def parse_gpu_mems(value: str, num_gpus: int | None) -> list[float]:
    parts = [p.strip() for p in value.split(",") if p.strip()]
    if not parts:
        raise argparse.ArgumentTypeError("--gpu-mem-gib must contain at least one number")
    mems = [float(p) for p in parts]
    if any(m <= 0 for m in mems):
        raise argparse.ArgumentTypeError("GPU memory values must be positive")
    if len(mems) == 1 and num_gpus:
        mems = mems * num_gpus
    elif num_gpus and len(mems) != num_gpus:
        raise argparse.ArgumentTypeError("when --num-gpus is set, --gpu-mem-gib must be one value or exactly num-gpus values")
    return mems


def make_plan(stages: list[str], gpu_mems: list[float], headroom: float, streaming: bool, latency: bool) -> list[StagePlan]:
    plans: list[StagePlan] = []
    per_gpu_counts = {i: 0 for i in range(len(gpu_mems))}
    assignments: list[int] = []
    for idx, _ in enumerate(stages):
        device = idx % len(gpu_mems)
        assignments.append(device)
        per_gpu_counts[device] += 1

    for idx, (name, device) in enumerate(zip(stages, assignments)):
        total = gpu_mems[device]
        share_count = per_gpu_counts[device]
        usable_per_stage = max((total - headroom) / max(share_count, 1), total * 0.05)
        util = max(0.04, min(0.95, round(usable_per_stage / total, 3)))
        lower = name.lower()
        is_generation = any(tok in lower for tok in ["dit", "diffusion", "vae", "code2wav", "vocoder", "decoder", "generation"])
        notes: list[str] = []
        if share_count > 1:
            notes.append(f"GPU {device} is shared by {share_count} planned stages; validate peak memory under load.")
        if streaming:
            notes.append("async_chunk/streaming workloads need headroom for in-flight stage handoff buffers.")
        if is_generation:
            notes.append("generation/diffusion/vocoder stages are often eager and memory-sensitive; tune after first warmup.")
        else:
            notes.append("AR stages can often use CUDA graphs unless debugging or dynamic shapes force eager mode.")
        plans.append(
            StagePlan(
                stage_id=idx,
                name=name,
                device=str(device),
                gpu_memory_utilization=util,
                max_num_seqs_hint=16 if is_generation else 32,
                enforce_eager_hint=True if is_generation else False,
                async_scheduling_hint=True if (streaming or latency) else False,
                notes=notes,
            )
        )
    return plans


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan rough vLLM-Omni stage placement without loading models.")
    parser.add_argument("--stages", required=True, help="Comma-separated stage names, e.g. thinker,talker,code2wav")
    parser.add_argument("--num-gpus", type=int, default=None, help="GPU count when --gpu-mem-gib is a single repeated value")
    parser.add_argument("--gpu-mem-gib", required=True, help="Single memory value or comma-separated per-GPU GiB values")
    parser.add_argument("--headroom-gib", type=float, default=1.5, help="Memory to leave free on each GPU before splitting")
    parser.add_argument("--streaming", action="store_true", help="Include async-chunk streaming headroom notes")
    parser.add_argument("--low-latency", action="store_true", help="Prefer async scheduling hints for latency-oriented services")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    stages = [s.strip() for s in args.stages.split(",") if s.strip()]
    if not stages:
        parser.error("--stages must name at least one stage")
    if args.num_gpus is not None and args.num_gpus < 1:
        parser.error("--num-gpus must be positive")
    gpu_mems = parse_gpu_mems(args.gpu_mem_gib, args.num_gpus)
    plans = make_plan(stages, gpu_mems, args.headroom_gib, args.streaming, args.low_latency)

    if args.format == "json":
        print(json.dumps([asdict(p) for p in plans], indent=2))
        return 0

    print("stage_id name device gpu_memory_utilization max_num_seqs enforce_eager async_scheduling")
    for p in plans:
        print(
            f"{p.stage_id:<8} {p.name:<16} {p.device:<6} {p.gpu_memory_utilization:<22} "
            f"{p.max_num_seqs_hint:<12} {str(p.enforce_eager_hint):<13} {str(p.async_scheduling_hint):<16}"
        )
        for note in p.notes:
            print(f"  - {note}")
    print("\nUse these as overlay starting values, then validate with the real model, workload, and peak-memory logs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
