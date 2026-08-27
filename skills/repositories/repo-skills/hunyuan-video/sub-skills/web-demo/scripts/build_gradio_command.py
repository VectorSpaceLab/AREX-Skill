#!/usr/bin/env python3
"""Build a safe HunyuanVideo Gradio launch command without starting a server."""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Dict, List


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a HunyuanVideo Gradio launch command using the bundled runner.")
    parser.add_argument("--repo-root", default=None, help="Optional HunyuanVideo source root; omit when hyvideo is installed/importable.")
    parser.add_argument("--runner", default=None, help="Path to bundled run_gradio_server.py; defaults to sub-skills/web-demo/scripts/run_gradio_server.py.")
    parser.add_argument("--model-base", default="ckpts")
    parser.add_argument("--save-path", default="./results")
    parser.add_argument("--server-name", default="127.0.0.1", help="Use 0.0.0.0 only when external access is intentional.")
    parser.add_argument("--server-port", type=int, default=7860)
    parser.add_argument("--flow-reverse", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.server_port <= 0 or args.server_port > 65535:
        parser.error("server port must be in 1..65535")
    if args.runner is None:
        args.runner = "sub-skills/web-demo/scripts/run_gradio_server.py"

    env: Dict[str, str] = {
        "GRADIO_ANALYTICS_ENABLED": "False",
        "SERVER_NAME": args.server_name,
        "SERVER_PORT": str(args.server_port),
    }
    cmd: List[str] = ["python", args.runner]
    if args.repo_root:
        cmd += ["--repo-root", args.repo_root]
    cmd += [
        "--model-base", args.model_base,
        "--save-path", args.save_path,
    ]
    if args.flow_reverse:
        cmd.append("--flow-reverse")
    shell = " ".join(f"{k}={shlex.quote(v)}" for k, v in env.items()) + " " + shlex.join(cmd)
    if args.json:
        print(json.dumps({"env": env, "command": cmd, "shell": shell}, indent=2))
    else:
        print(shell)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
