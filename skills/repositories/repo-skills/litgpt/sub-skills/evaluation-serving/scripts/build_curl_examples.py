#!/usr/bin/env python3
"""Generate curl examples for LitGPT LitServe endpoint modes.

This script only prints request examples. It does not start a server or send any
network requests.
"""

from __future__ import annotations

import argparse
import json
import sys


def ensure_path(value: str) -> str:
    if not value.startswith("/"):
        raise argparse.ArgumentTypeError("api path must start with '/'")
    return value


def build_url(host: str, port: int, path: str) -> str:
    scheme_host = host if host.startswith(("http://", "https://")) else f"http://{host}"
    return f"{scheme_host}:{port}{path}"


def json_for_shell(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def simple_curl(url: str, prompt: str, stream: bool) -> str:
    payload = {"prompt": prompt}
    no_buffer = " -N" if stream else ""
    return (
        f"curl{no_buffer} -X POST {url} \\\n"
        "  -H 'Content-Type: application/json' \\\n"
        f"  -d '{json_for_shell(payload)}'"
    )


def openai_curl(url: str, model: str, prompt: str, stream: bool) -> str:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    if stream:
        payload["stream"] = True
    no_buffer = " -N" if stream else ""
    return (
        f"curl{no_buffer} -X POST {url} \\\n"
        "  -H 'Content-Type: application/json' \\\n"
        f"  -d '{json_for_shell(payload)}'"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print LitGPT curl examples for simple, stream, and OpenAI-compatible modes.")
    parser.add_argument("--mode", choices=["simple", "stream", "openai", "openai-stream", "all"], default="all")
    parser.add_argument("--host", default="127.0.0.1", help="server host without port, with or without http(s) scheme")
    parser.add_argument("--port", type=int, default=8000, help="server port")
    parser.add_argument("--api-path", type=ensure_path, default="/predict", help="simple API path or OpenAI chat completions path")
    parser.add_argument("--openai-api-path", type=ensure_path, default="/v1/chat/completions", help="OpenAI-compatible chat completions path when --mode all")
    parser.add_argument("--model", default="local-litgpt-model", help="model field for OpenAI-compatible requests")
    parser.add_argument("--prompt", default="Hello from LitGPT!", help="prompt or user message content")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.port <= 0 or args.port > 65535:
        print("error: --port must be between 1 and 65535", file=sys.stderr)
        return 2

    sections: list[tuple[str, str, str]] = []
    simple_url = build_url(args.host, args.port, args.api_path)
    openai_path = args.api_path if args.mode in {"openai", "openai-stream"} else args.openai_api_path
    openai_url = build_url(args.host, args.port, openai_path)

    if args.mode in {"simple", "all"}:
        sections.append((
            "Simple prompt API",
            "Start with: litgpt serve CHECKPOINT_DIR --api_path " + args.api_path + f" --port {args.port}",
            simple_curl(simple_url, args.prompt, stream=False),
        ))
    if args.mode in {"stream", "all"}:
        sections.append((
            "Simple streaming API",
            "Start with: litgpt serve CHECKPOINT_DIR --stream true --api_path " + args.api_path + f" --port {args.port}",
            simple_curl(simple_url, args.prompt, stream=True),
        ))
    if args.mode in {"openai", "all"}:
        sections.append((
            "OpenAI-compatible chat completions API",
            f"Start with: litgpt serve CHECKPOINT_DIR --openai_spec true --port {args.port}",
            openai_curl(openai_url, args.model, args.prompt, stream=False),
        ))
    if args.mode in {"openai-stream", "all"}:
        sections.append((
            "OpenAI-compatible streaming chat completions API",
            f"Start with: litgpt serve CHECKPOINT_DIR --openai_spec true --port {args.port}",
            openai_curl(openai_url, args.model, args.prompt, stream=True),
        ))

    for index, (title, command, curl) in enumerate(sections):
        if index:
            print()
        print(f"## {title}")
        print(command)
        print(curl)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
