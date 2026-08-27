#!/usr/bin/env python3
"""Compute mixtral-offloading OffloadConfig sizes without importing the repo."""
from __future__ import annotations

import argparse
import json
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--num-hidden-layers', type=int, required=True, help='Transformer layer count from the Mixtral config.')
    parser.add_argument('--num-experts', type=int, required=True, help='Experts per layer from the Mixtral config.')
    parser.add_argument('--offload-per-layer', type=int, required=True, help='Experts per layer to keep off-device.')
    parser.add_argument('--buffer-size', type=int, default=4, help='Temporary swap buffer count; demo default is 4.')
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    warnings: list[str] = []
    if args.num_hidden_layers <= 0:
        warnings.append('num_hidden_layers must be positive')
    if args.num_experts <= 0:
        warnings.append('num_experts must be positive')
    if args.buffer_size <= 0:
        warnings.append('buffer_size should be positive for overlapped swaps')
    if args.offload_per_layer < 0:
        warnings.append('offload_per_layer cannot be negative')
    if args.offload_per_layer > args.num_experts:
        warnings.append('offload_per_layer exceeds num_experts; main_size would be negative')

    main_per_layer = args.num_experts - args.offload_per_layer
    main_size = args.num_hidden_layers * main_per_layer
    offload_size = args.num_hidden_layers * args.offload_per_layer
    if main_per_layer <= 0:
        warnings.append('no experts remain on-device per layer; cache eviction/swap paths may fail')
    if args.offload_per_layer == 0:
        warnings.append('no experts are offloaded; this maximizes VRAM use')

    payload = {
        'main_size': main_size,
        'offload_size': offload_size,
        'buffer_size': args.buffer_size,
        'offload_per_layer': args.offload_per_layer,
        'main_experts_per_layer': main_per_layer,
        'warnings': warnings,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 1 if any('must' in w or 'cannot' in w or 'exceeds' in w for w in warnings) else 0


if __name__ == '__main__':
    raise SystemExit(main())
