#!/usr/bin/env python3
"""Build ColossalAI inference command templates without executing them."""
import argparse
import shlex


def q(cmd):
    return " ".join(shlex.quote(x) for x in cmd)


def main():
    ap = argparse.ArgumentParser(description="Generate safe ColossalAI inference command templates.")
    sub = ap.add_subparsers(dest="kind", required=True)
    llama = sub.add_parser("llama", help="LLM/LLaMA generation command anatomy")
    llama.add_argument("--model", required=True)
    llama.add_argument("--script", default="llama_generation.py")
    llama.add_argument("--nproc-per-node", type=int, default=1)
    llama.add_argument("--tp-size", type=int, default=1)
    llama.add_argument("--max-length", type=int, default=128)
    llama.add_argument("--drafter-model")
    diff = sub.add_parser("diffusion", help="Stable Diffusion 3 command anatomy")
    diff.add_argument("--model", required=True)
    diff.add_argument("--script", default="sd3_generation.py")
    diff.add_argument("--prompt", default="hello world")
    diff.add_argument("--nproc-per-node", type=int, default=1)
    args = ap.parse_args()
    if args.kind == "llama":
        cmd = ["colossalai", "run", "--nproc_per_node", str(args.nproc_per_node), args.script, "-m", args.model, "--max_length", str(args.max_length)]
        if args.tp_size != 1:
            cmd += ["--tp_size", str(args.tp_size)]
        if args.drafter_model:
            cmd += ["--drafter_model", args.drafter_model]
        if args.tp_size != args.nproc_per_node:
            print("warning: tp-size differs from nproc-per-node; ensure the script supports this layout")
        print(q(cmd))
    else:
        cmd = ["colossalai", "run", "--nproc_per_node", str(args.nproc_per_node), args.script, "-m", args.model, "-p", args.prompt]
        print(q(cmd))


if __name__ == "__main__":
    main()
