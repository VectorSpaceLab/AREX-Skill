#!/usr/bin/env python3
"""Plan mixtral-offloading ExpertCache capacities without loading model weights."""
from __future__ import annotations

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--num-hidden-layers', type=int, required=True)
    parser.add_argument('--num-experts', type=int, required=True)
    parser.add_argument('--offload-per-layer', type=int, required=True)
    parser.add_argument('--buffer-size', type=int, default=4)
    parser.add_argument('--examples', type=int, default=4, help='Number of example UIDs to include.')
    args = parser.parse_args()

    warnings: list[str] = []
    if args.num_hidden_layers <= 0:
        warnings.append('num_hidden_layers must be positive')
    if args.num_experts <= 0:
        warnings.append('num_experts must be positive')
    if args.offload_per_layer < 0:
        warnings.append('offload_per_layer cannot be negative')
    if args.offload_per_layer > args.num_experts:
        warnings.append('offload_per_layer exceeds num_experts')
    if args.buffer_size <= 0:
        warnings.append('buffer_size should be positive')

    main_per_layer = args.num_experts - args.offload_per_layer
    offloaded_per_layer = args.offload_per_layer
    if main_per_layer <= 0:
        warnings.append('no main expert remains per layer; swaps may have no evictable expert')

    main_uids = []
    offloaded_uids = []
    for layer in range(max(args.num_hidden_layers, 0)):
        for expert in range(max(args.num_experts, 0)):
            uid = [layer, expert]
            if expert < args.offload_per_layer:
                offloaded_uids.append(uid)
            else:
                main_uids.append(uid)

    payload = {
        'main_size': args.num_hidden_layers * main_per_layer,
        'offload_size': args.num_hidden_layers * offloaded_per_layer,
        'buffer_size': args.buffer_size,
        'main_experts_per_layer': main_per_layer,
        'offloaded_experts_per_layer': offloaded_per_layer,
        'eviction_groups': args.num_hidden_layers,
        'example_main_uids': main_uids[: args.examples],
        'example_offloaded_uids': offloaded_uids[: args.examples],
        'warnings': warnings,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 1 if any('must' in w or 'cannot' in w or 'exceeds' in w for w in warnings) else 0


if __name__ == '__main__':
    raise SystemExit(main())
