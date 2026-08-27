#!/usr/bin/env python3
"""Build a safe DeepSpeed config JSON for OpenFold training."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Optional


def maybe_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    return float(value)


def build_config(args: argparse.Namespace) -> Dict[str, Any]:
    enabled_precision_modes = sum([args.fp16, args.bfloat16, args.amp])
    if enabled_precision_modes > 1:
        raise ValueError("enable at most one of --fp16, --bfloat16, or --amp")

    config: Dict[str, Any] = {}

    if args.gradient_clipping is not None:
        config["gradient_clipping"] = args.gradient_clipping

    if args.optimizer:
        optimizer_params: Dict[str, Any] = {"lr": args.lr, "eps": args.eps}
        if args.optimizer == "OneBitAdam":
            optimizer_params.update(
                {
                    "freeze_step": args.freeze_step,
                    "cuda_aware": args.cuda_aware,
                    "comm_backend_name": args.comm_backend_name,
                }
            )
        config["optimizer"] = {"type": args.optimizer, "params": optimizer_params}

    if args.scheduler:
        scheduler_params: Dict[str, Any]
        if args.scheduler == "WarmupLR":
            scheduler_params = {
                "warmup_min_lr": args.warmup_min_lr,
                "warmup_max_lr": args.warmup_max_lr,
                "warmup_num_steps": args.warmup_num_steps,
            }
        elif args.scheduler == "WarmupDecayLR":
            scheduler_params = {
                "warmup_min_lr": args.warmup_decay_min_lr,
                "warmup_max_lr": args.warmup_decay_max_lr,
                "warmup_num_steps": args.warmup_decay_num_steps,
                "total_num_steps": args.warmup_decay_total_num_steps,
            }
        elif args.scheduler == "OneCycle":
            scheduler_params = {
                "cycle_min_lr": args.cycle_min_lr,
                "cycle_max_lr": args.cycle_max_lr,
                "decay_lr_rate": args.cycle_decay_lr_rate,
                "cycle_first_step_size": args.cycle_first_step_size,
                "cycle_second_step_size": args.cycle_second_step_size,
                "cycle_momentum": args.cycle_momentum,
                "cycle_min_mom": args.cycle_min_mom,
                "cycle_max_mom": args.cycle_max_mom,
                "decay_mom_rate": args.cycle_decay_mom_rate,
            }
        else:
            scheduler_params = {
                "lr_range_test_min_lr": args.lr_range_test_min_lr,
                "lr_range_test_step_size": args.lr_range_test_step_size,
                "lr_range_test_step_rate": args.lr_range_test_step_rate,
                "lr_range_test_staircase": args.lr_range_test_staircase,
            }
        config["scheduler"] = {"type": args.scheduler, "params": scheduler_params}

    if args.bfloat16:
        config["bfloat16"] = {"enabled": True}
    elif args.fp16:
        config["fp16"] = {"enabled": True, "min_loss_scale": args.fp16_min_loss_scale}
    elif args.amp:
        config["amp"] = {"enabled": True, "opt_level": args.amp_opt_level}

    config["zero_optimization"] = {
        "stage": args.zero_stage,
        "allgather_partitions": args.allgather_partitions,
        "allgather_bucket_size": args.allgather_bucket_size,
        "reduce_bucket_size": args.reduce_bucket_size,
        "overlap_comm": args.overlap_comm,
        "reduce_scatter": args.reduce_scatter,
        "contiguous_gradients": args.contiguous_gradients,
    }
    if args.offload_optimizer:
        config["zero_optimization"]["offload_optimizer"] = {
            "device": "cpu",
            "pin_memory": args.pin_memory,
        }

    config["activation_checkpointing"] = {
        "partition_activations": args.partition_activations,
        "cpu_checkpointing": args.cpu_checkpointing,
        "profile": args.profile_activation_checkpointing,
    }

    if args.flops_profiler:
        config["flops_profiler"] = {
            "enabled": True,
            "profile_step": args.profile_step,
            "module_depth": args.module_depth,
            "top_modules": args.top_modules,
            "detailed": args.detailed_flops_profile,
        }

    if args.zero_force_ds_cpu_optimizer is not None:
        config["zero_force_ds_cpu_optimizer"] = args.zero_force_ds_cpu_optimizer

    return config


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Emit a standalone DeepSpeed config JSON for OpenFold training without importing DeepSpeed."
    )
    parser.add_argument("--output", help="Write JSON to this path instead of stdout")
    parser.add_argument("--gradient-clipping", type=float, default=0.1)

    optimizer = parser.add_argument_group("optimizer")
    optimizer.add_argument("--optimizer", choices=["Adam", "OneBitAdam"])
    optimizer.add_argument("--lr", type=float, default=1e-3)
    optimizer.add_argument("--eps", type=float, default=1e-8)
    optimizer.add_argument("--freeze-step", type=int, default=100)
    optimizer.add_argument("--cuda-aware", action="store_true")
    optimizer.add_argument("--comm-backend-name", default="nccl", choices=["nccl", "mpi"])

    scheduler = parser.add_argument_group("scheduler")
    scheduler.add_argument("--scheduler", choices=["LRRangeTest", "OneCycle", "WarmupLR", "WarmupDecayLR"])
    scheduler.add_argument("--lr-range-test-min-lr", type=float, default=1e-4)
    scheduler.add_argument("--lr-range-test-step-size", type=int, default=2000)
    scheduler.add_argument("--lr-range-test-step-rate", type=float, default=1.0)
    scheduler.add_argument("--lr-range-test-staircase", action="store_true")
    scheduler.add_argument("--cycle-min-lr", type=float, default=1e-6)
    scheduler.add_argument("--cycle-max-lr", type=float, default=1e-3)
    scheduler.add_argument("--cycle-decay-lr-rate", type=float, default=0.0)
    scheduler.add_argument("--cycle-first-step-size", type=int, default=2000)
    scheduler.add_argument("--cycle-second-step-size", type=int)
    scheduler.add_argument("--cycle-momentum", dest="cycle_momentum", action="store_true")
    scheduler.add_argument("--no-cycle-momentum", dest="cycle_momentum", action="store_false")
    scheduler.set_defaults(cycle_momentum=True)
    scheduler.add_argument("--cycle-min-mom", type=float, default=0.8)
    scheduler.add_argument("--cycle-max-mom", type=float, default=0.9)
    scheduler.add_argument("--cycle-decay-mom-rate", type=float, default=0.0)
    scheduler.add_argument("--warmup-min-lr", type=float, default=0.0)
    scheduler.add_argument("--warmup-max-lr", type=float, default=1e-3)
    scheduler.add_argument("--warmup-num-steps", type=int, default=1000)
    scheduler.add_argument("--warmup-decay-min-lr", type=float, default=0.0)
    scheduler.add_argument("--warmup-decay-max-lr", type=float, default=1e-3)
    scheduler.add_argument("--warmup-decay-num-steps", type=int, default=1000)
    scheduler.add_argument("--warmup-decay-total-num-steps", type=int, default=100000)

    precision = parser.add_argument_group("precision")
    precision.add_argument("--bfloat16", action="store_true", help="Enable DeepSpeed BF16; preferred on supported A100-class GPUs")
    precision.add_argument("--fp16", action="store_true", help="Enable DeepSpeed FP16; do not pair with train_openfold.py --precision 16")
    precision.add_argument("--fp16-min-loss-scale", type=int, default=1)
    precision.add_argument("--amp", action="store_true")
    precision.add_argument("--amp-opt-level", default="O2")

    zero = parser.add_argument_group("zero optimization")
    zero.add_argument("--zero-stage", type=int, default=2, choices=[0, 1, 2, 3])
    zero.add_argument("--allgather-partitions", action="store_true")
    zero.add_argument("--allgather-bucket-size", type=float, default=1e9)
    zero.add_argument("--reduce-bucket-size", type=float, default=1e9)
    zero.add_argument("--overlap-comm", action="store_true")
    zero.add_argument("--reduce-scatter", action="store_true")
    zero.add_argument("--contiguous-gradients", dest="contiguous_gradients", action="store_true")
    zero.add_argument("--no-contiguous-gradients", dest="contiguous_gradients", action="store_false")
    zero.set_defaults(contiguous_gradients=True)
    zero.add_argument("--offload-optimizer", action="store_true")
    zero.add_argument("--pin-memory", action="store_true")
    zero.add_argument("--zero-force-ds-cpu-optimizer", dest="zero_force_ds_cpu_optimizer", action="store_true")
    zero.add_argument("--no-zero-force-ds-cpu-optimizer", dest="zero_force_ds_cpu_optimizer", action="store_false")
    zero.set_defaults(zero_force_ds_cpu_optimizer=None)

    activation = parser.add_argument_group("activation checkpointing")
    activation.add_argument("--partition-activations", action="store_true")
    activation.add_argument("--cpu-checkpointing", action="store_true")
    activation.add_argument("--profile-activation-checkpointing", action="store_true")

    profiler = parser.add_argument_group("flops profiler")
    profiler.add_argument("--flops-profiler", action="store_true")
    profiler.add_argument("--profile-step", type=int, default=1)
    profiler.add_argument("--module-depth", type=int, default=-1)
    profiler.add_argument("--top-modules", type=int, default=3)
    profiler.add_argument("--detailed-flops-profile", action="store_true")
    return parser


def main() -> int:
    args = parser().parse_args()
    try:
        config = build_config(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    text = json.dumps(config, indent=2, sort_keys=True) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
