#!/usr/bin/env python3
"""Suggest a ColossalAI Booster plugin from high-level requirements."""
import argparse
import math


def main():
    ap = argparse.ArgumentParser(description="Suggest a ColossalAI Booster plugin and important follow-up checks.")
    ap.add_argument("--gpus", type=int, default=1, help="Total launched GPU/process count.")
    ap.add_argument("--need-pipeline", action="store_true", help="Need pipeline parallelism.")
    ap.add_argument("--need-tensor", action="store_true", help="Need tensor parallelism.")
    ap.add_argument("--need-moe", action="store_true", help="Need expert parallel / MoE training.")
    ap.add_argument("--memory-pressure", choices=["low", "optimizer", "parameters", "extreme"], default="low")
    ap.add_argument("--cpu-offload", action="store_true", help="Prefer CPU offload to reduce GPU memory.")
    args = ap.parse_args()
    notes = ["Initialize distributed state before constructing the plugin."]
    if args.need_moe:
        plugin = "MoeHybridParallelPlugin(tp_size=..., pp_size=..., ep_size=..., zero_stage=...)"
        notes.append("Choose ep_size/tp_size/pp_size so they divide the world size.")
    elif args.need_pipeline or args.need_tensor:
        plugin = "HybridParallelPlugin(tp_size=..., pp_size=..., zero_stage=...)"
        notes.append("Define a pipeline criterion and use booster.execute_pipeline when pp_size > 1.")
    elif args.memory_pressure in {"extreme", "parameters"}:
        plugin = "GeminiPlugin(placement_policy='static' or tuned placement/offload knobs)"
        notes.append("Tune shard/offload fractions and verify optional fused kernels separately.")
    elif args.memory_pressure == "optimizer" or args.cpu_offload:
        stage = 2 if args.cpu_offload else 1
        plugin = f"LowLevelZeroPlugin(stage={stage}, cpu_offload={args.cpu_offload})"
    elif args.gpus > 1:
        plugin = "TorchDDPPlugin()"
    else:
        plugin = "TorchDDPPlugin() for a first Booster smoke; plain PyTorch may be enough if no distributed feature is required."
    print("Suggested plugin:", plugin)
    print("Follow-up checks:")
    for note in notes:
        print("-", note)


if __name__ == "__main__":
    main()
