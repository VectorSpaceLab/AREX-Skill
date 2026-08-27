#!/usr/bin/env python3
"""Render a safe HunyuanImage-3.0 Gradio launch command.

This helper mirrors the app launch wrapper without starting Gradio, opening a
port, importing the model, or downloading checkpoints. It validates the launch
inputs that are easy to check safely and prints the command a user could run
after the app import path has been repaired or confirmed healthy.
"""

from __future__ import annotations

import argparse
import os
import shlex
import sys
from pathlib import Path

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 443
DEFAULT_GPUS = "0,1,2,3"
PLACEHOLDER_MODEL_IDS = {
    "HunyuanImage-3/",
    "./HunyuanImage-3",
    "path/to/your/model",
    "MODEL_ID",
}


def _env_or_arg(value: str | None, env_name: str, default: str | None = None) -> str | None:
    if value not in (None, ""):
        return value
    env_value = os.environ.get(env_name)
    if env_value not in (None, ""):
        return env_value
    return default


def _validate_model_id(raw_model_id: str | None, *, allow_missing_path: bool) -> str:
    if raw_model_id is None or raw_model_id.strip() == "":
        raise SystemExit("MODEL_ID is required; pass --model-id or set MODEL_ID to a local checkpoint directory.")

    model_id = raw_model_id.strip()
    if model_id in PLACEHOLDER_MODEL_IDS:
        raise SystemExit(
            f"MODEL_ID looks like a placeholder ({model_id!r}); provide a real local checkpoint directory."
        )

    if not allow_missing_path:
        path = Path(model_id)
        if not path.exists():
            raise SystemExit(f"MODEL_ID path does not exist: {model_id}")
        if not path.is_dir():
            raise SystemExit(f"MODEL_ID must point to a checkpoint directory: {model_id}")

    return model_id


def _validate_port(raw_port: int | str | None) -> int:
    try:
        port = int(raw_port if raw_port is not None else DEFAULT_PORT)
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"PORT must be an integer, got {raw_port!r}") from exc
    if not 1 <= port <= 65535:
        raise SystemExit(f"PORT must be between 1 and 65535, got {port}")
    return port


def render_exports(gpus: str) -> list[str]:
    return [
        f"export CUDA_VISIBLE_DEVICES={shlex.quote(gpus)}",
        "export http_proxy=",
        "export https_proxy=",
        "export GRADIO_ANALYTICS_ENABLED=False",
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render, but do not execute, a HunyuanImage-3.0 Gradio app launch command.",
        epilog=(
            "Unknown arguments are passed through to the app command, for example "
            "--moe-impl eager --attn-impl sdpa --image-cache-dir ./cache."
        ),
    )
    parser.add_argument("--model-id", help="Local checkpoint directory. Falls back to the MODEL_ID environment variable.")
    parser.add_argument("--host", help=f"Server host. Falls back to HOST or {DEFAULT_HOST!r}.")
    parser.add_argument("--port", help=f"Server port. Falls back to PORT or {DEFAULT_PORT}.")
    parser.add_argument("--gpus", help=f"GPU id list. Falls back to GPUS or {DEFAULT_GPUS!r}.")
    parser.add_argument(
        "--allow-missing-path",
        action="store_true",
        help="Render the command even if --model-id does not exist locally. Use only for planning text.",
    )
    parser.add_argument(
        "--no-open-sidebar",
        dest="open_sidebar",
        action="store_false",
        default=True,
        help="Do not include --open-sidebar in the rendered app command.",
    )

    args, passthrough = parser.parse_known_args(argv)

    host = _env_or_arg(args.host, "HOST", DEFAULT_HOST)
    port = _validate_port(_env_or_arg(args.port, "PORT", str(DEFAULT_PORT)))
    gpus = _env_or_arg(args.gpus, "GPUS", DEFAULT_GPUS) or DEFAULT_GPUS
    model_id = _validate_model_id(
        _env_or_arg(args.model_id, "MODEL_ID"),
        allow_missing_path=args.allow_missing_path,
    )

    command = ["python3", "app/run_chatbot.py"]
    if args.open_sidebar:
        command.append("--open-sidebar")
    command.extend(["--host", str(host), "--port", str(port), "--model-id", model_id])
    command.extend(passthrough)

    print("# HunyuanImage-3.0 Gradio app preflight")
    print(f"MODEL_ID: {model_id}")
    print(f"HOST: {host}")
    print(f"PORT: {port}")
    print(f"GPUS: {gpus}")
    if port < 1024:
        print("WARNING: selected port is privileged on many systems; use 7860 or 8080 if binding fails.")
    print("WARNING: this renderer does not repair the known stale app imports; run check_app_imports.py first.")
    print()
    print("# Environment exports")
    for line in render_exports(gpus):
        print(line)
    print()
    print("# Command")
    print(shlex.join(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
