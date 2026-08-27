#!/usr/bin/env python3
"""Print the paired Gradio launch command and its prerequisites.

This helper does not launch a server. It only reports the intended command.
"""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path

DEMO_MAP = {
    "canny": {
        "script": "gradio_canny2image.py",
        "selector": "edge_to_image",
        "share": "False",
        "risk": "imports the model at module load and may download the edge-to-image LoRA before the UI appears",
    },
    "sketch": {
        "script": "gradio_sketch2image.py",
        "selector": "sketch_to_image_stochastic",
        "share": "True",
        "risk": "imports the model at module load, may download the sketch LoRA before the UI appears, and exposes share=True in the source launch",
    },
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print the paired Gradio command for the canny or sketch demo along "
            "with the key prerequisites. The helper does not launch Gradio."
        )
    )
    parser.add_argument(
        "demo",
        choices=tuple(DEMO_MAP.keys()),
        help="which paired Gradio demo to print",
    )
    parser.add_argument(
        "--source_root",
        default=".",
        help="source checkout root to place after 'cd' in the printed command",
    )
    parser.add_argument(
        "--gradio_executable",
        default="gradio",
        help="gradio command name to print (default: gradio)",
    )
    parser.add_argument(
        "--command_only",
        action="store_true",
        help="print only the shell command, without prerequisite notes",
    )
    parser.add_argument(
        "--strict_paths",
        action="store_true",
        help="treat a missing source Gradio script as an error",
    )
    return parser


def shell_join(parts: list[str]) -> str:
    return " ".join(part if part == "&&" else shlex.quote(str(part)) for part in parts)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    meta = DEMO_MAP[args.demo]
    script_path = Path(args.source_root) / meta["script"]
    if not script_path.exists():
        message = f"paired Gradio script not found at {script_path}"
        if args.strict_paths:
            parser.error(message)
        if not args.command_only:
            print(f"warning: {message}")

    command = shell_join(["cd", args.source_root, "&&", args.gradio_executable, meta["script"]])
    if not args.command_only:
        print(f"# Paired Gradio demo: {args.demo}")
        print("# Prerequisites: a prepared source checkout, CUDA-capable PyTorch, the repo requirements, and permission to load/download the paired checkpoint.")
        print(f"# Source behavior: {meta['risk']}")
        print(f"# Source launch share setting: {meta['share']}")
    print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
