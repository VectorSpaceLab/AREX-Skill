#!/usr/bin/env python3
"""Safe Feast server command/config smoke checker.

The script validates local Feast CLI availability, checks server command choices,
optionally validates a feature repo config path, and prints next-step commands.
It does not launch long-running servers unless --run is explicitly provided.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

COMMANDS = {
    "serve": {
        "default_port": 6566,
        "description": "online feature server",
        "health": "/health",
    },
    "serve_offline": {
        "default_port": 8815,
        "description": "remote offline Arrow Flight server",
        "health": None,
    },
    "serve_registry": {
        "default_port": 6570,
        "description": "registry gRPC server",
        "health": None,
    },
    "serve_transformations": {
        "default_port": 6569,
        "description": "experimental transformation server",
        "health": None,
    },
}


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Feast server CLI/config and print safe server next steps.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-path",
        default=".",
        help="Feature repository directory containing feature_store.yaml, or a parent used with Feast --chdir.",
    )
    parser.add_argument(
        "--command",
        choices=sorted(COMMANDS),
        default="serve",
        help="Feast server command to plan or run.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Server bind host.")
    parser.add_argument(
        "--port",
        type=positive_int,
        default=None,
        help="Server port. Defaults to the selected Feast server default.",
    )
    parser.add_argument(
        "--server-type",
        choices=("http", "grpc"),
        default="http",
        help="Feature-server type for feast serve only.",
    )
    parser.add_argument(
        "--registry-ttl-sec",
        type=positive_int,
        default=60,
        help="Registry refresh interval for feast serve.",
    )
    parser.add_argument("--key", default="", help="TLS private key path for server startup.")
    parser.add_argument("--cert", default="", help="TLS public certificate path for server startup or client curl hints.")
    parser.add_argument(
        "--tls",
        action="store_true",
        help="Plan TLS mode. Requires --key and --cert for --run; warns otherwise.",
    )
    parser.add_argument(
        "--rest-api",
        action="store_true",
        help="For serve_registry, include the REST registry API.",
    )
    parser.add_argument(
        "--rest-port",
        type=positive_int,
        default=6572,
        help="REST registry port when --rest-api is used.",
    )
    parser.add_argument(
        "--no-grpc",
        action="store_true",
        help="For serve_registry, disable the default gRPC registry server.",
    )
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="For feast serve, include the metrics flag.",
    )
    parser.add_argument(
        "--print-curl",
        action="store_true",
        help="Print curl examples for feature-server routes.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Actually execute the planned Feast command. Without this, only prints the command.",
    )
    return parser


def find_config(repo_path: Path) -> Path | None:
    candidates = [repo_path / "feature_store.yaml", repo_path / "feature_store.yml"]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def run_capture(command: list[str]) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        return 127, "", str(exc)
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def validate_feast() -> int:
    feast_path = shutil.which("feast")
    if not feast_path:
        print("ERROR: Feast CLI entry point not found on PATH.", file=sys.stderr)
        print("Install Feast in the active environment and verify with `feast --help`.", file=sys.stderr)
        return 2

    print(f"Feast CLI: {feast_path}")
    code, stdout, stderr = run_capture([feast_path, "--help"])
    if code != 0:
        print("ERROR: `feast --help` failed.", file=sys.stderr)
        if stderr:
            print(stderr, file=sys.stderr)
        return 2

    try:
        import feast  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on user env
        print(f"WARNING: Python import `feast` failed: {exc}", file=sys.stderr)
        print("The CLI may point at a different Python environment.", file=sys.stderr)
    else:
        print(f"Python feast: {getattr(feast, '__version__', 'unknown')}")

    return 0


def validate_paths(args: argparse.Namespace, repo_path: Path) -> int:
    status = 0
    config_path = find_config(repo_path)
    if config_path:
        print(f"Config: {config_path}")
    else:
        print(
            f"WARNING: no feature_store.yaml found under {repo_path}. "
            "Server startup may fail unless --chdir points at a valid repo.",
            file=sys.stderr,
        )

    key = Path(args.key).expanduser() if args.key else None
    cert = Path(args.cert).expanduser() if args.cert else None
    wants_tls = args.tls or bool(args.key or args.cert)

    if bool(key) != bool(cert):
        print("ERROR: TLS mode requires both --key and --cert.", file=sys.stderr)
        status = 2
    if wants_tls and not (key and cert):
        print("WARNING: TLS was requested but --key/--cert are not both set.", file=sys.stderr)
    if key and not key.exists():
        print(f"ERROR: TLS key does not exist: {key}", file=sys.stderr)
        status = 2
    if cert and not cert.exists():
        print(f"ERROR: TLS cert does not exist: {cert}", file=sys.stderr)
        status = 2

    if args.command != "serve_registry" and args.no_grpc:
        print("WARNING: --no-grpc only applies to serve_registry.", file=sys.stderr)
    if args.command != "serve_registry" and args.rest_api:
        print("WARNING: --rest-api only applies to serve_registry.", file=sys.stderr)
    if args.command != "serve" and args.server_type != "http":
        print("WARNING: --server-type only applies to feast serve.", file=sys.stderr)

    return status


def planned_command(args: argparse.Namespace, repo_path: Path) -> list[str]:
    port = args.port or COMMANDS[args.command]["default_port"]
    command = ["feast", "--chdir", str(repo_path), args.command]

    if args.command == "serve":
        command.extend(
            [
                "--host",
                args.host,
                "--port",
                str(port),
                "--type",
                args.server_type,
                "--registry_ttl_sec",
                str(args.registry_ttl_sec),
            ]
        )
        if args.metrics:
            command.append("--metrics")
    elif args.command == "serve_offline":
        command.extend(["--host", args.host, "--port", str(port)])
    elif args.command == "serve_registry":
        if not args.no_grpc:
            command.extend(["--port", str(port)])
        if args.no_grpc:
            command.append("--no-grpc")
        if args.rest_api:
            command.extend(["--rest-api", "--rest-port", str(args.rest_port)])
    elif args.command == "serve_transformations":
        command.extend(["--port", str(port)])

    if args.key and args.cert and args.command != "serve_transformations":
        command.extend(["--key", args.key, "--cert", args.cert])

    return command


def shell_join(parts: Iterable[str]) -> str:
    return " ".join(sh_quote(part) for part in parts)


def sh_quote(value: str) -> str:
    if not value:
        return "''"
    safe = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_+-=/:.,@%")
    if all(char in safe for char in value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"


def print_next_steps(args: argparse.Namespace, command: list[str]) -> None:
    port = args.port or COMMANDS[args.command]["default_port"]
    scheme = "https" if args.key and args.cert else "http"
    print("\nPlanned command:")
    print(shell_join(command))

    print("\nSafe next steps:")
    if args.command == "serve":
        print(f"- Health check: curl -fsS {scheme}://{args.host}:{port}/health")
        print("- Online request: POST /get-online-features with JSON features/entities.")
        print("- If auth is enabled: add `Authorization: Bearer <token>`.")
        if args.print_curl:
            cert_arg = f" --cacert {sh_quote(args.cert)}" if args.cert else ""
            print("\nCurl examples:")
            print(f"curl -fsS{cert_arg} {scheme}://{args.host}:{port}/health")
            print(
                "curl -sS"
                f"{cert_arg} -X POST {scheme}://{args.host}:{port}/get-online-features "
                "-H 'Content-Type: application/json' "
                "-d '{\"features\":[\"driver_hourly_stats:conv_rate\"],\"entities\":{\"driver_id\":[1001]}}'"
            )
    elif args.command == "serve_offline":
        arrow_scheme = "grpc+tls" if args.key and args.cert else "grpc+tcp"
        print(f"- Expected listen URI: {arrow_scheme}://{args.host}:{port}")
        print("- Client config: `offline_store: {type: remote, host: ..., port: ...}`.")
        if args.key and args.cert:
            print("- TLS client config also needs `scheme: https` and `cert: <ca/public cert>`.")
    elif args.command == "serve_registry":
        if not args.no_grpc:
            print(f"- gRPC registry: {args.host}:{port}")
        if args.rest_api:
            print(f"- REST registry port: {args.rest_port}")
        print("- Client config: `registry: {registry_type: remote, path: host:port}`.")
    elif args.command == "serve_transformations":
        print(f"- Transformation server port: {port}")

    print("- This script did not start a server. Re-run with --run to execute the command.")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    repo_path = Path(args.repo_path).expanduser().resolve()

    status = validate_feast()
    path_status = validate_paths(args, repo_path)
    status = max(status, path_status)

    command = planned_command(args, repo_path)
    print_next_steps(args, command)

    if status != 0:
        return status

    if args.run:
        print("\nRunning command. Stop with Ctrl+C when finished.")
        try:
            return subprocess.call(command)
        except KeyboardInterrupt:
            print("Interrupted.", file=sys.stderr)
            return 130

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
