#!/usr/bin/env python3
"""Statically verify the checked-in CLI argument and chat-call contract.

No repository imports, checkpoint loads, network requests, or interactive
input are performed.
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path


def fail(message: str) -> "NoReturn":
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify cli_demo.py flags and chat wiring without loading a model."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="repository root containing cli_demo.py (default: infer from this script)",
    )
    return parser.parse_args()


def infer_root() -> Path:
    return Path(__file__).resolve().parents[6]


def calls_and_parser_nodes(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Call, ast.Assign, ast.AnnAssign, ast.AugAssign)):
            yield node


def main() -> int:
    args = parse_args()
    root = (args.repo_root or infer_root()).expanduser().resolve()
    path = root / "cli_demo.py"
    if not path.is_file():
        fail(f"missing cli_demo.py under {root}")
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError) as exc:
        fail(f"cannot parse cli_demo.py: {exc}")

    flags = {}
    for node in calls_and_parser_nodes(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "add_argument" or not node.args:
            continue
        first = node.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            keyword = {kw.arg: kw.value for kw in node.keywords if kw.arg}
            flags[first.value] = keyword

    required = {
        "--max_length",
        "--top_p",
        "--top_k",
        "--temperature",
        "--english",
        "--quant",
        "--from_pretrained",
        "--prompt_zh",
        "--prompt_en",
    }
    missing = sorted(required - flags.keys())
    if missing:
        fail("missing CLI flags: " + ", ".join(missing))
    quant_choices = flags["--quant"].get("choices")
    if not isinstance(quant_choices, ast.List) or [
        elt.value if isinstance(elt, ast.Constant) else None for elt in quant_choices.elts
    ] != [8, 4]:
        fail("--quant must expose choices [8, 4]")
    if "action" not in flags["--english"]:
        fail("--english must be an action flag")

    chat_call = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "chat":
            names = {kw.arg for kw in node.keywords if kw.arg}
            if {"history", "image", "max_length", "top_p", "temperature", "top_k", "english"}.issubset(names):
                chat_call = True
                break
    if not chat_call:
        fail("could not find chat() call with history/image/sampling wiring")
    for literal in ("clear", "stop", "--from_pretrained"):
        if literal not in source:
            fail(f"CLI source lacks expected interaction marker {literal!r}")
    print(f"PASS: CLI flags, quantization choices, interaction markers, and chat wiring under {root}")
    return 0


if __name__ == "__main__":
    main()
