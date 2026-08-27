#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex

DTYPES = ("auto", "bfloat16", "float16", "float32")
QUANTS = ("none", "int8", "nf4")


def add(cmd, flag, value):
    if value not in (None, ""):
        cmd.extend([flag, str(value)])


def extend(cmd, flag, values):
    vals = [v for v in (values or []) if v]
    if vals:
        cmd.append(flag)
        cmd.extend(vals)


def parser():
    p = argparse.ArgumentParser(description="Print a Petals run_server command without launching a server.")
    p.add_argument("--mode", choices=("public", "private"), required=True)
    p.add_argument("model", nargs="?")
    p.add_argument("--model", dest="model_opt")
    p.add_argument("--config")
    p.add_argument("--public-name")
    p.add_argument("--num-blocks", type=int)
    p.add_argument("--block-indices")
    p.add_argument("--dht-prefix")
    p.add_argument("--port", type=int)
    p.add_argument("--public-ip")
    p.add_argument("--device")
    p.add_argument("--torch-dtype", choices=DTYPES)
    p.add_argument("--cache-dir")
    p.add_argument("--max-disk-space")
    p.add_argument("--throughput")
    p.add_argument("--initial-peer", action="append")
    p.add_argument("--new-swarm", action="store_true")
    p.add_argument("--identity-path")
    p.add_argument("--quant-type", choices=QUANTS)
    p.add_argument("--tensor-parallel-devices", action="append")
    p.add_argument("--adapter", action="append")
    p.add_argument("--skip-reachability-check", action="store_true")
    return p


def main():
    p = parser()
    a = p.parse_args()
    model = a.model or a.model_opt
    if bool(a.model) == bool(a.model_opt):
        p.error("provide exactly one model: positional MODEL or --model")
    if a.public_ip and not a.port:
        p.error("--public-ip requires non-zero --port")
    if a.num_blocks and a.block_indices:
        p.error("--num-blocks conflicts with --block-indices")
    if a.initial_peer and a.new_swarm:
        p.error("--initial-peer conflicts with --new-swarm")
    if a.mode == "public" and (a.initial_peer or a.new_swarm):
        p.error("public mode uses default peers; omit private peer flags")
    if a.mode == "private" and not (a.initial_peer or a.new_swarm):
        p.error("private mode needs --initial-peer or --new-swarm")
    if a.block_indices:
        try:
            start, end = map(int, a.block_indices.split(":"))
        except Exception:
            p.error("--block-indices must be START:END")
        if start < 0 or end <= start:
            p.error("--block-indices range is invalid")
    cmd = ["python", "-m", "petals.cli.run_server"]
    add(cmd, "--config", a.config)
    cmd.append(model)
    for flag, val in [
        ("--public_name", a.public_name),
        ("--num_blocks", a.num_blocks),
        ("--block_indices", a.block_indices),
        ("--dht_prefix", a.dht_prefix),
        ("--port", a.port),
        ("--public_ip", a.public_ip),
        ("--device", a.device),
        ("--torch_dtype", a.torch_dtype),
        ("--cache_dir", a.cache_dir),
        ("--max_disk_space", a.max_disk_space),
        ("--throughput", a.throughput),
        ("--identity_path", a.identity_path),
        ("--quant_type", a.quant_type),
    ]:
        add(cmd, flag, val)
    extend(cmd, "--initial_peers", a.initial_peer)
    if a.new_swarm:
        cmd.append("--new_swarm")
    extend(cmd, "--tensor_parallel_devices", a.tensor_parallel_devices)
    extend(cmd, "--adapters", a.adapter)
    if a.skip_reachability_check:
        cmd.append("--skip_reachability_check")
    print(shlex.join(cmd))


if __name__ == "__main__":
    main()
