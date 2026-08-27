#!/usr/bin/env python3
"""Generate LEANN MCP client JSON or an HTTP serve command without launching it."""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import shlex
import sys
from pathlib import Path
from typing import Sequence


SERVER_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
RUN_MCP_IN_DIRECTORY = (
    "import os,runpy,sys;"
    "os.chdir(sys.argv[1]);"
    "sys.argv=['leann_mcp'];"
    "runpy.run_module('leann.mcp',run_name='__main__')"
)


class ConfigError(ValueError):
    """Raised for invalid or unsafe requested output."""


def _plain_value(value: str, label: str) -> str:
    if not value:
        raise ConfigError(f"{label} must not be empty")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ConfigError(f"{label} must not contain control characters")
    return value


def _server_name(value: str) -> str:
    if not SERVER_NAME_RE.fullmatch(value):
        raise argparse.ArgumentTypeError(
            "server name must be 1-64 characters using letters, digits, '.', '_', or '-', "
            "and must start with a letter or digit"
        )
    return value


def _port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("port must be an integer") from exc
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def _project_directory(raw: str) -> str:
    _plain_value(raw, "project directory")
    path = Path(raw).expanduser()
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ConfigError(f"project directory does not exist or cannot be resolved: {raw}") from exc
    if not resolved.is_dir():
        raise ConfigError(f"project directory is not a directory: {raw}")
    return str(resolved)


def _is_loopback(host: str) -> bool:
    normalized = host.strip().lower()
    if normalized == "localhost":
        return True
    candidate = normalized[1:-1] if normalized.startswith("[") and normalized.endswith("]") else normalized
    try:
        return ipaddress.ip_address(candidate).is_loopback
    except ValueError:
        return False


def _mcp_server_spec(args: argparse.Namespace) -> dict[str, object]:
    entrypoint = _plain_value(args.entrypoint_command, "entrypoint command")
    python_command = _plain_value(args.python_command, "Python command")

    if args.project_dir:
        if args.launch == "entrypoint":
            raise ConfigError(
                "--project-dir cannot be combined with --launch entrypoint: the verified "
                "LEANN --base-dir option does not apply the child working directory; use "
                "--launch auto or --launch module"
            )
        project_dir = _project_directory(args.project_dir)
        command = python_command
        command_args = ["-c", RUN_MCP_IN_DIRECTORY, project_dir]
    elif args.launch == "module":
        command = python_command
        command_args = ["-m", "leann.mcp"]
    else:
        command = entrypoint
        command_args = []

    # Keep the runtime object deliberately minimal. In particular, do not copy
    # ambient credentials into generated JSON.
    return {"command": command, "args": command_args, "env": {}}


def _emit_mcp(args: argparse.Namespace) -> str:
    # The verified Claude/OpenClaw patterns all use the mcpServers object. The
    # client choice is explicit for review even though the JSON shape is shared.
    del args.client
    document = {"mcpServers": {args.server_name: _mcp_server_spec(args)}}
    indent = None if args.compact else 2
    return json.dumps(document, indent=indent, ensure_ascii=False, sort_keys=True)


def _emit_http(args: argparse.Namespace) -> str:
    host = _plain_value(args.host.strip(), "host")
    executable = _plain_value(args.command, "HTTP command")

    if any(char.isspace() for char in host):
        raise ConfigError("host must not contain whitespace")
    if not _is_loopback(host) and not args.allow_network_exposure:
        raise ConfigError(
            "refusing a non-loopback bind without --allow-network-exposure; LEANN's HTTP "
            "service has no built-in authentication or TLS"
        )

    argv = [executable, "serve", "--host", host, "--port", str(args.port)]
    if args.format == "json-argv":
        return json.dumps(argv, ensure_ascii=False)
    return shlex.join(argv)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a LEANN MCP client configuration or HTTP serve command. "
            "This helper validates and prints output only; it never launches a service."
        )
    )
    subparsers = parser.add_subparsers(dest="kind", required=True)

    mcp = subparsers.add_parser(
        "mcp",
        help="emit a strict JSON mcpServers configuration",
        description=(
            "Emit strict JSON for a generic MCP client, Claude Code/Desktop, or OpenClaw. "
            "No credentials are copied into the output."
        ),
    )
    mcp.add_argument(
        "--client",
        choices=("generic", "claude-code", "claude-desktop", "openclaw"),
        default="generic",
        help="target client for review purposes; all verified targets use mcpServers JSON",
    )
    mcp.add_argument(
        "--server-name",
        type=_server_name,
        default="leann",
        help="configuration key for the server (default: leann)",
    )
    mcp.add_argument(
        "--launch",
        choices=("auto", "entrypoint", "module"),
        default="auto",
        help=(
            "auto uses leann_mcp unless --project-dir is set; module uses the selected "
            "Python interpreter; entrypoint cannot be project-pinned (default: auto)"
        ),
    )
    mcp.add_argument(
        "--entrypoint-command",
        default="leann_mcp",
        help="MCP executable used by entrypoint launch (default: leann_mcp)",
    )
    mcp.add_argument(
        "--python-command",
        default="python",
        help="Python executable name/path used by module launch (default: python)",
    )
    mcp.add_argument(
        "--project-dir",
        help=(
            "existing project root to set before module launch; preserved as one JSON arg, "
            "including spaces"
        ),
    )
    mcp.add_argument(
        "--compact",
        action="store_true",
        help="emit one-line JSON instead of indented JSON",
    )
    mcp.set_defaults(render=_emit_mcp)

    http = subparsers.add_parser(
        "http",
        help="emit a shell-escaped leann serve command without running it",
    )
    http.add_argument(
        "--command",
        default="leann",
        help="LEANN CLI executable name/path (default: leann)",
    )
    http.add_argument(
        "--host",
        default="127.0.0.1",
        help="bind host (default: 127.0.0.1)",
    )
    http.add_argument(
        "--port",
        type=_port,
        default=8000,
        help="bind port, 1-65535 (default: 8000)",
    )
    http.add_argument(
        "--allow-network-exposure",
        action="store_true",
        help=(
            "allow a non-loopback host after external authentication/TLS/firewall review; "
            "this flag adds no protection"
        ),
    )
    http.add_argument(
        "--format",
        choices=("shell", "json-argv"),
        default="shell",
        help="output a shell-escaped command or JSON argv array (default: shell)",
    )
    http.set_defaults(render=_emit_http)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        output = args.render(args)
    except ConfigError as exc:
        parser.error(str(exc))
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
