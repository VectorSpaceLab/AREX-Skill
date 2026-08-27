#!/usr/bin/env python3
"""Print a safe Qwen local launch plan; never load a model or start a service."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description="Build a dry-run Qwen CLI/Web/OpenAI API command.")
    p.add_argument("--mode", choices=["cli", "web", "openai-api"], required=True)
    p.add_argument("--checkpoint", required=True, help="Model id or local checkpoint path.")
    p.add_argument("--server-name", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--seed", type=int, default=1234)
    p.add_argument("--cpu-only", action="store_true")
    p.add_argument("--share", action="store_true", help="Plan a public Gradio share link; does not create one.")
    p.add_argument("--auth", help="BasicAuth username:password for API planning only.")
    args = p.parse_args()

    path = Path(args.checkpoint).expanduser()
    local = path.exists()
    if local and not path.is_dir():
        p.error("--checkpoint exists but is not a directory")
    if local and not (path / "config.json").exists():
        print("WARNING: local checkpoint has no config.json; loading will fail until the path is corrected.")
    if not local and ("/" in args.checkpoint or "\\" in args.checkpoint):
        print("WARNING: checkpoint looks like a local path but does not exist; no download is attempted.")

    flags = ["-c", args.checkpoint]
    if args.cpu_only:
        flags.append("--cpu-only")
    if args.mode == "cli":
        flags += ["--seed", str(args.seed)]
        command = "python cli_demo.py " + " ".join(flags)
    elif args.mode == "web":
        flags += ["--server-name", args.server_name, "--server-port", str(args.port)]
        if args.share:
            flags.append("--share")
        command = "python web_demo.py " + " ".join(flags)
    else:
        flags += ["--server-name", args.server_name, "--server-port", str(args.port)]
        if args.auth:
            flags += ["--api-auth", args.auth]
        command = "python openai_api.py " + " ".join(flags)
    print("DRY RUN (not executed):")
    print(command)
    print("Prerequisites: trusted checkpoint, required optional dependencies, and deliberate network/port exposure.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
