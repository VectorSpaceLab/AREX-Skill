#!/usr/bin/env python3
"""Build a safe BentoML serve command without running it."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path


def _add_option(command: list[str], flag: str, value: object | None) -> None:
    if value is not None:
        command.extend([flag, str(value)])


def build_command(args: argparse.Namespace) -> list[str]:
    command = ["bentoml", "serve-grpc" if args.grpc else "serve", args.target]
    if args.development:
        command.append("--development")
    if args.reload:
        command.append("--reload")
    _add_option(command, "--working-dir", args.working_dir)
    _add_option(command, "--host", args.host)
    _add_option(command, "--port", args.port)
    _add_option(command, "--api-workers", args.api_workers)
    _add_option(command, "--backlog", args.backlog)
    if not args.grpc:
        _add_option(command, "--timeout", args.timeout)
    if args.grpc:
        if args.enable_reflection:
            command.append("--enable-reflection")
        if args.enable_channelz:
            command.append("--enable-channelz")
        _add_option(command, "--max-concurrent-streams", args.max_concurrent_streams)
        _add_option(command, "--protocol-version", args.protocol_version)
    for item in args.arg or []:
        command.extend(["--arg", item])
    for item in args.arg_file or []:
        command.extend(["--arg-file", item])
    return command


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print a shell-safe bentoml serve command. This script does not start a server."
    )
    parser.add_argument("target", help="Service import target, Bento tag, or Bento directory")
    parser.add_argument("--grpc", action="store_true", help="Build a bentoml serve-grpc command")
    parser.add_argument("--development", action="store_true", help="Add --development")
    parser.add_argument("--reload", action="store_true", help="Add --reload")
    parser.add_argument("--working-dir", help="Directory used for service imports")
    parser.add_argument("--host", help="Bind host")
    parser.add_argument("--port", type=int, help="Bind port")
    parser.add_argument("--api-workers", type=int, help="Number of API workers")
    parser.add_argument("--backlog", type=int, help="Maximum pending connections")
    parser.add_argument("--timeout", type=int, help="HTTP API server and runner timeout")
    parser.add_argument("--enable-reflection", action="store_true", help="gRPC reflection flag")
    parser.add_argument("--enable-channelz", action="store_true", help="gRPC channelz flag")
    parser.add_argument("--max-concurrent-streams", type=int, help="gRPC stream limit")
    parser.add_argument("--protocol-version", choices=("v1", "v1alpha1"), help="gRPC protocol version")
    parser.add_argument("--arg", action="append", help="Template/build argument; may be repeated")
    parser.add_argument("--arg-file", action="append", help="Template/build argument file; may be repeated")
    parser.add_argument("--check-working-dir", action="store_true", help="Warn if --working-dir does not exist")
    args = parser.parse_args()

    if args.check_working_dir and args.working_dir and not Path(args.working_dir).is_dir():
        print(f"warning: working directory does not exist: {args.working_dir}")
    print(shlex.join(build_command(args)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
