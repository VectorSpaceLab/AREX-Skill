#!/usr/bin/env python3
"""Inspect the ChatGLM2-6B multi-GPU layer map without loading model weights."""
from __future__ import annotations

import argparse
import json


def build_map(num_gpus: int) -> dict[str, int]:
    if num_gpus < 1:
        raise ValueError("--num-gpus must be at least 1")
    if num_gpus == 1:
        return {
            "transformer.embedding.word_embeddings": 0,
            "transformer.encoder.final_layernorm": 0,
            "transformer.output_layer": 0,
            "transformer.rotary_pos_emb": 0,
            "lm_head": 0,
            **{f"transformer.encoder.layers.{i}": 0 for i in range(28)},
        }
    per_gpu_layers = 30 / num_gpus
    device_map = {
        "transformer.embedding.word_embeddings": 0,
        "transformer.encoder.final_layernorm": 0,
        "transformer.output_layer": 0,
        "transformer.rotary_pos_emb": 0,
        "lm_head": 0,
    }
    used = 2
    gpu_target = 0
    for i in range(28):
        if used >= per_gpu_layers:
            gpu_target += 1
            used = 0
        if gpu_target >= num_gpus:
            raise ValueError("computed map exceeded --num-gpus; inspect the requested device count")
        device_map[f"transformer.encoder.layers.{i}"] = gpu_target
        used += 1
    return device_map


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--num-gpus", type=int, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        device_map = build_map(args.num_gpus)
    except ValueError as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(device_map, indent=2, sort_keys=True))
        return 0
    by_gpu: dict[int, list[str]] = {}
    for name, gpu in device_map.items():
        by_gpu.setdefault(gpu, []).append(name)
    print(f"entries: {len(device_map)}")
    for gpu in sorted(by_gpu):
        layers = by_gpu[gpu]
        print(f"cuda:{gpu}: {len(layers)} modules")
        for name in layers:
            print(f"  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
