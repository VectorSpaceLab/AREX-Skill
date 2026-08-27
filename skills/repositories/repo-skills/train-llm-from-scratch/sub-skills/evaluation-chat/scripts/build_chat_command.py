#!/usr/bin/env python3
"""Dry-run command builder for train-llm-from-scratch chat/raw inference.

The script prints commands only. It never loads a model, opens a checkpoint, or
starts the interactive REPL itself.
"""

from __future__ import annotations

import argparse
import shlex


def shell_words(words: list[str]) -> str:
    return " ".join(shlex.quote(str(w)) for w in words)


def python_words(python: str) -> list[str]:
    parts = shlex.split(python)
    return parts or ["python"]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Print a dry-run PYTHONPATH=. python scripts/chat.py command for one-shot or REPL inference."
    )
    p.add_argument("--ckpt", required=True, help="checkpoint path")
    p.add_argument("--prompt", help="one-shot prompt; omit to build an interactive REPL command")
    p.add_argument("--system", help="optional system message for chat mode")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--raw", action="store_true", help="raw base-model continuation with no chat template")
    mode.add_argument("--chat", action="store_true", help="explicit chat-template mode (default)")
    p.add_argument("--max_new_tokens", type=int, default=256, help="generation budget (default: 256)")
    p.add_argument("--temperature", type=float, default=0.8, help="sampling temperature (default: 0.8)")
    p.add_argument("--top_p", type=float, default=0.95, help="nucleus sampling threshold (default: 0.95)")
    p.add_argument("--top_k", type=int, default=None, help="top-k sampling cutoff")
    p.add_argument("--greedy", action="store_true", help="deterministic argmax decoding")
    p.add_argument("--device", help="device to pass through, e.g. cuda or cpu")
    p.add_argument("--python", default="python", help="python executable command to print (default: python)")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.max_new_tokens <= 0:
        parser.error("--max_new_tokens must be positive")
    if args.temperature <= 0:
        parser.error("--temperature must be positive")
    if args.top_p <= 0:
        parser.error("--top_p must be positive")
    if args.top_k is not None and args.top_k <= 0:
        parser.error("--top_k must be positive when supplied")
    if args.raw and args.system:
        parser.error("--system is a chat-mode option; remove it or omit --raw")

    cmd = ["PYTHONPATH=.", *python_words(args.python), "scripts/chat.py", "--ckpt", args.ckpt]
    if args.prompt is not None:
        cmd += ["--prompt", args.prompt]
    if args.system:
        cmd += ["--system", args.system]
    if args.raw:
        cmd.append("--raw")
    cmd += ["--max_new_tokens", str(args.max_new_tokens)]
    if args.greedy:
        cmd.append("--greedy")
    else:
        cmd += ["--temperature", str(args.temperature), "--top_p", str(args.top_p)]
        if args.top_k is not None:
            cmd += ["--top_k", str(args.top_k)]
    if args.device:
        cmd += ["--device", args.device]

    print("# dry run: chat/raw inference command (not executed)")
    print("# mode: " + ("raw continuation" if args.raw else "chat template"))
    print("# interface: " + ("one-shot" if args.prompt is not None else "interactive REPL"))
    print(shell_words(cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
