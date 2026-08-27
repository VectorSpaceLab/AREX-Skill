#!/usr/bin/env python3
"""Build a `colossalai run` command without executing it."""
import argparse
import shlex
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="Generate a safe ColossalAI launcher command.")
    ap.add_argument("--script", required=True, help="Training script path or module name when --module is used.")
    ap.add_argument("--module", action="store_true", help="Use `-m` module mode instead of a .py script path.")
    ap.add_argument("--nproc-per-node", type=int, required=True, help="Worker processes per node, usually GPUs per node.")
    ap.add_argument("--master-addr", default="127.0.0.1", help="Rendezvous address.")
    ap.add_argument("--master-port", type=int, default=29500, help="Rendezvous port.")
    ap.add_argument("--host", help="Comma-separated host list.")
    ap.add_argument("--hostfile", help="Hostfile with one host per line.")
    ap.add_argument("--include", help="Comma-separated host filter for hostfile launches.")
    ap.add_argument("--exclude", help="Comma-separated host filter for hostfile launches.")
    ap.add_argument("--num-nodes", type=int, help="Limit number of hostfile nodes.")
    ap.add_argument("--extra-launch-args", help="Comma-separated torch launcher args, e.g. standalone,rdzv_backend=c10d.")
    ap.add_argument("user_args", nargs=argparse.REMAINDER, help="Arguments after `--` are passed to the user script.")
    args = ap.parse_args()
    if args.include and args.exclude:
        raise SystemExit("--include and --exclude are mutually exclusive")
    if args.host and args.hostfile:
        raise SystemExit("Use either --host or --hostfile, not both")
    if args.hostfile and not Path(args.hostfile).exists():
        raise SystemExit(f"hostfile does not exist: {args.hostfile}")
    if args.module and args.script.endswith(".py"):
        raise SystemExit("--module expects a module name, not a .py file")
    cmd = ["colossalai", "run", "--nproc_per_node", str(args.nproc_per_node), "--master_addr", args.master_addr, "--master_port", str(args.master_port)]
    for flag, value in [("--host", args.host), ("--hostfile", args.hostfile), ("--include", args.include), ("--exclude", args.exclude), ("--extra_launch_args", args.extra_launch_args)]:
        if value:
            cmd += [flag, value]
    if args.num_nodes:
        cmd += ["--num_nodes", str(args.num_nodes)]
    cmd += (["-m", args.script] if args.module else [args.script])
    user_args = args.user_args[1:] if args.user_args[:1] == ["--"] else args.user_args
    cmd += user_args
    print(" ".join(shlex.quote(x) for x in cmd))


if __name__ == "__main__":
    main()
