#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex

DTYPES = ("auto", "bfloat16", "float16", "float32")


def q(cmd):
    return shlex.join(cmd)


def main():
    p = argparse.ArgumentParser(description="Print a private Petals DHT/server command plan without launching processes.")
    p.add_argument("--model", required=True)
    p.add_argument("--bootstrap-port", type=int, default=31337)
    p.add_argument("--bootstrap-identity", default="bootstrap.id")
    p.add_argument("--bootstrap-host", default="127.0.0.1")
    p.add_argument("--server-count", type=int, default=1)
    p.add_argument("--device", default="cpu")
    p.add_argument("--torch-dtype", choices=DTYPES, default="float32")
    p.add_argument("--blocks-per-server", type=int)
    p.add_argument("--start-block", type=int, default=0)
    p.add_argument("--cache-dir")
    p.add_argument("--throughput", default="1")
    p.add_argument("--loopback-only", action="store_true")
    a = p.parse_args()
    if not (1 <= a.bootstrap_port <= 65535):
        p.error("bad bootstrap port")
    if a.server_count < 1:
        p.error("--server-count must be positive")
    if a.loopback_only and a.bootstrap_host not in ("127.0.0.1", "localhost"):
        p.error("--loopback-only requires loopback host")
    dht = [
        "python",
        "-m",
        "petals.cli.run_dht",
        "--identity_path",
        a.bootstrap_identity,
        "--host_maddrs",
        f"/ip4/{a.bootstrap_host}/tcp/{a.bootstrap_port}",
    ]
    peer = f"/ip4/{a.bootstrap_host}/tcp/{a.bootstrap_port}/p2p/PEER_ID_FROM_BOOTSTRAP"
    print("# Petals private swarm plan; nothing was launched")
    print("# Replace PEER_ID_FROM_BOOTSTRAP with the DHT peer id printed by the bootstrap process.")
    print(q(dht))
    print("export INITIAL_PEERS=" + shlex.quote(peer))
    for i in range(a.server_count):
        cmd = [
            "python",
            "-m",
            "petals.cli.run_server",
            a.model,
            "--initial_peers",
            "$INITIAL_PEERS",
            "--identity_path",
            f"server-{i}.id",
            "--device",
            a.device,
            "--torch_dtype",
            a.torch_dtype,
            "--throughput",
            a.throughput,
        ]
        if a.cache_dir:
            cmd += ["--cache_dir", (a.cache_dir.rstrip("/") + f"/server-{i}") if a.server_count > 1 else a.cache_dir]
        if a.blocks_per_server:
            start = a.start_block + i * a.blocks_per_server
            cmd += ["--block_indices", f"{start}:{start + a.blocks_per_server}"]
        if a.loopback_only:
            cmd += ["--host_maddrs", f"/ip4/127.0.0.1/tcp/{a.bootstrap_port + i + 1}"]
        print(q(cmd).replace("'$INITIAL_PEERS'", '"$INITIAL_PEERS"'))


if __name__ == "__main__":
    main()
