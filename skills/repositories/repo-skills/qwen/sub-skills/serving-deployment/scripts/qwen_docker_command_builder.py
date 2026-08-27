#!/usr/bin/env python3
"""Build Qwen Docker commands without pulling images or running containers."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description="Build a dry-run Qwen Docker CLI/Web/OpenAI API command.")
    p.add_argument("--mode", choices=["cli", "web", "openai-api"], required=True)
    p.add_argument("--checkpoint", required=True, help="Host checkpoint directory.")
    p.add_argument("--image", default="qwenllm/qwen:cu117")
    p.add_argument("--container", default="qwen")
    p.add_argument("--port", type=int, default=None)
    p.add_argument("--no-validate", action="store_true", help="Do not inspect local config.json.")
    args = p.parse_args()

    checkpoint = Path(args.checkpoint).expanduser()
    if not args.no_validate:
        if not checkpoint.is_dir():
            p.error("checkpoint directory does not exist; use --no-validate only for a template")
        if not (checkpoint / "config.json").is_file():
            p.error("checkpoint directory does not contain config.json")

    mount = "/data/shared/Qwen/Qwen-Chat"
    if args.mode == "cli":
        command = f"docker run --gpus all --rm --name {args.container} --mount type=bind,source={checkpoint},target={mount} -it {args.image} python cli_demo.py -c {mount}/"
    else:
        port = args.port or (8901 if args.mode == "web" else 8000)
        program = "web_demo.py" if args.mode == "web" else "openai_api.py"
        command = f"docker run --gpus all -d --restart always --name {args.container} -p {port}:80 --mount type=bind,source={checkpoint},target={mount} -it {args.image} python {program} --server-port 80 --server-name 0.0.0.0 -c {mount}/"
    print("DRY RUN (not executed):")
    print(command)
    print("Prerequisites: Docker, NVIDIA Container Toolkit, compatible driver/image, and deliberate port exposure.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
