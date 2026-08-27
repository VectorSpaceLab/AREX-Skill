#!/usr/bin/env python3
"""Statically verify the XrayGLM Gradio WebUI contract.

This check never imports Gradio, loads weights, opens a browser, or launches a
server. It parses source and checks the small callback/argument surface.
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
        description="Verify web_demo.py flags and Gradio callback wiring without launching it."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="repository root containing web_demo.py (default: infer from this script)",
    )
    return parser.parse_args()


def infer_root() -> Path:
    return Path(__file__).resolve().parents[6]


def main() -> int:
    args = parse_args()
    root = (args.repo_root or infer_root()).expanduser().resolve()
    path = root / "web_demo.py"
    if not path.is_file():
        fail(f"missing web_demo.py under {root}")
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError) as exc:
        fail(f"cannot parse web_demo.py: {exc}")

    parser_flags = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "add_argument" or not node.args:
            continue
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            parser_flags.add(arg.value)
    for flag in ("--quant", "--share", "--from_pretrained"):
        if flag not in parser_flags:
            fail(f"WebUI parser is missing {flag}")

    if 'choices=[8, 4]' not in source:
        fail("WebUI quantization choices are not [8, 4]")
    required_text = (
        'gr.Image(type="filepath"',
        "temperature = gr.Slider",
        "top_p = gr.Slider",
        "run_button.click",
        "input_text.submit",
        "clear_button.click",
        "demo.launch",
        "share=args.share",
    )
    for marker in required_text:
        if marker not in source:
            fail(f"WebUI source lacks expected contract marker {marker!r}")

    callback_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            callback_names.add(node.name)
    if "request_model" not in callback_names or "generate_text_with_image" not in callback_names:
        fail("WebUI callback functions are missing")
    print(f"PASS: WebUI flags, filepath image input, sliders, callbacks, and launch wiring under {root}")
    return 0


if __name__ == "__main__":
    main()
