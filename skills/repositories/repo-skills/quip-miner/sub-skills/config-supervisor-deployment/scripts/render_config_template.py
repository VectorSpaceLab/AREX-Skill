#!/usr/bin/env python3
"""Render a minimal quip-miner TOML config template."""
from __future__ import annotations

import argparse


def _miner_header(args: argparse.Namespace) -> list[str]:
    lines = ["[miner]"]
    if args.validator:
        vals = ", ".join(repr(v).replace("'", '"') for v in args.validator)
        lines.append(f"validators = [{vals}]")
    lines.append(f"signer_key = {args.signer_key!r}".replace("'", '"'))
    if args.rest_port is not None:
        lines.append(f"rest_host = {args.rest_host!r}".replace("'", '"'))
        lines.append(f"rest_port = {int(args.rest_port)}")
    if args.node_name:
        lines.append(f"node_name = {args.node_name!r}".replace("'", '"'))
    return lines


def render(args: argparse.Namespace) -> str:
    lines = _miner_header(args)
    lines.append("")
    if args.backend == "cpu":
        lines.extend(["[cpu]", f"num_cpus = {args.num_cpus}"])
        if args.pow_only:
            lines.append("mempool = false")
    elif args.backend == "cuda":
        lines.extend(["[gpu]", f"utilization = {args.utilization}", f"yielding = {str(args.yielding).lower()}"])
        if args.pow_only:
            lines.append("mempool = false")
        for dev in args.cuda_devices.split(","):
            dev = dev.strip()
            if dev:
                lines.extend(["", f"[cuda.{dev}]"])
    elif args.backend == "metal":
        lines.extend(["[metal]", f"utilization = {args.utilization}", "yielding = true", f"active_util = {args.active_util}"])
        if args.pow_only:
            lines.append("mempool = false")
    elif args.backend == "modal":
        lines.extend(["[modal]", f"gpu_type = {args.gpu_type!r}".replace("'", '"')])
        if args.pow_only:
            lines.append("mempool = false")
    elif args.backend == "dwave":
        lines.extend(["[dwave]", f"daily_budget = {args.daily_budget!r}".replace("'", '"'), "# solver = \"Advantage2_system1\"", "# region = \"na-west-1\""])
        if args.mempool:
            lines.append("mempool = true")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("cpu", "cuda", "metal", "modal", "dwave"), default="cpu")
    parser.add_argument("--validator", action="append", help="Validator URL; repeat for failover.")
    parser.add_argument("--signer-key", default="~/.quip-miner/signing.json")
    parser.add_argument("--rest-host", default="127.0.0.1")
    parser.add_argument("--rest-port", type=int, help="Enable REST telemetry on this port.")
    parser.add_argument("--node-name")
    parser.add_argument("--num-cpus", type=int, default=1)
    parser.add_argument("--cuda-devices", default="0")
    parser.add_argument("--utilization", type=int, default=100)
    parser.add_argument("--yielding", action="store_true")
    parser.add_argument("--active-util", type=int, default=85)
    parser.add_argument("--gpu-type", default="a10g")
    parser.add_argument("--daily-budget", default="30m")
    parser.add_argument("--pow-only", action="store_true", help="Disable default-on mempool for CPU/GPU sections.")
    parser.add_argument("--mempool", action="store_true", help="Opt QPU backend into mempool participation.")
    args = parser.parse_args()
    print(render(args), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
