#!/usr/bin/env python3
"""Validate mcp-agent MCP server configuration without starting servers.

The script performs static checks only by default. Use --check-executables to
verify stdio commands are present on PATH. Use --strict-package-model when the
runtime has mcp-agent installed and you want Pydantic settings validation too.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

VALID_TRANSPORTS = {"stdio", "sse", "streamable_http", "websocket"}
REMOTE_TRANSPORTS = {"sse", "streamable_http", "websocket"}
SENSITIVE_KEYS = {"authorization", "x-api-key", "api-key", "token"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Statically validate mcp-agent mcp.servers configuration."
    )
    parser.add_argument("config", help="Path to mcp_agent.config.yaml or JSON config")
    parser.add_argument(
        "--expect-server",
        action="append",
        default=[],
        help="Require a server key to exist; may be passed more than once.",
    )
    parser.add_argument(
        "--check-executables",
        action="store_true",
        help="Check stdio command executables with shutil.which without starting them.",
    )
    parser.add_argument(
        "--strict-package-model",
        action="store_true",
        help="Also instantiate mcp_agent.config.Settings when mcp-agent is installed.",
    )
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Return a non-zero exit code when warnings are present.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser


def load_document(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()
    if path.suffix.lower() == ".json" or stripped.startswith(("{", "[")):
        data = json.loads(text)
    else:
        try:
            import yaml  # type: ignore
        except Exception as exc:  # pragma: no cover - depends on environment
            raise RuntimeError(
                "YAML config requires PyYAML in this environment; install PyYAML or pass JSON."
            ) from exc
        data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise ValueError("Top-level config must be a mapping/object.")
    return data


def issue(severity: str, where: str, message: str) -> dict[str, str]:
    return {"severity": severity, "where": where, "message": message}


def is_placeholder(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    return (
        stripped.startswith("${")
        or stripped.startswith("!secret")
        or stripped.startswith("!user_secret")
        or stripped.startswith("!developer_secret")
        or stripped.startswith("<")
        or "${" in stripped
    )


def validate_url_scheme(
    value: Any, allowed: set[str], where: str, issues: list[dict[str, str]]
) -> None:
    if not isinstance(value, str) or not value:
        issues.append(issue("error", where, "URL must be a non-empty string."))
        return
    parsed = urlparse(value)
    if parsed.scheme not in allowed:
        issues.append(
            issue(
                "error",
                where,
                f"URL scheme '{parsed.scheme or '<none>'}' is invalid; expected one of {sorted(allowed)}.",
            )
        )


def validate_headers(
    headers: Any, where: str, issues: list[dict[str, str]]
) -> None:
    if headers is None:
        return
    if not isinstance(headers, dict):
        issues.append(issue("error", where, "headers must be a mapping."))
        return
    for key, value in headers.items():
        key_text = str(key).lower()
        if not isinstance(value, str):
            issues.append(issue("error", f"{where}.{key}", "header values must be strings."))
            continue
        looks_sensitive = any(marker in key_text for marker in SENSITIVE_KEYS)
        if looks_sensitive and value and not is_placeholder(value):
            issues.append(
                issue(
                    "warning",
                    f"{where}.{key}",
                    "sensitive header appears literal; prefer an environment or secrets placeholder.",
                )
            )


def validate_roots(roots: Any, where: str, issues: list[dict[str, str]]) -> None:
    if roots is None:
        return
    if not isinstance(roots, list):
        issues.append(issue("error", where, "roots must be a list."))
        return
    for index, root in enumerate(roots):
        root_where = f"{where}[{index}]"
        if not isinstance(root, dict):
            issues.append(issue("error", root_where, "root entry must be a mapping."))
            continue
        uri = root.get("uri")
        if not isinstance(uri, str) or not uri.startswith("file://"):
            issues.append(issue("error", f"{root_where}.uri", "root uri must start with file://."))
        alias = root.get("server_uri_alias")
        if alias is not None and (not isinstance(alias, str) or not alias.startswith("file://")):
            issues.append(
                issue(
                    "error",
                    f"{root_where}.server_uri_alias",
                    "server_uri_alias must start with file:// when present.",
                )
            )


def validate_oauth(oauth: Any, where: str, issues: list[dict[str, str]]) -> None:
    if oauth is None:
        return
    if not isinstance(oauth, dict):
        issues.append(issue("error", where, "oauth must be a mapping."))
        return
    if oauth.get("enabled") is not True:
        issues.append(issue("warning", where, "oauth block is present but enabled is not true."))
    if oauth.get("client_secret") and not is_placeholder(oauth.get("client_secret")):
        issues.append(
            issue(
                "warning",
                f"{where}.client_secret",
                "client_secret appears literal; prefer secrets or environment placeholders.",
            )
        )
    if oauth.get("include_resource_parameter", True) and not oauth.get("resource"):
        issues.append(
            issue(
                "warning",
                f"{where}.resource",
                "include_resource_parameter defaults to true; set resource or explicitly disable it for providers that reject resource.",
            )
        )
    redirects = oauth.get("redirect_uri_options")
    if redirects is not None and not isinstance(redirects, list):
        issues.append(issue("error", f"{where}.redirect_uri_options", "must be a list."))


def validate_server(
    name: str,
    server: Any,
    *,
    check_executables: bool,
    issues: list[dict[str, str]],
) -> None:
    where = f"mcp.servers.{name}"
    if not isinstance(server, dict):
        issues.append(issue("error", where, "server entry must be a mapping."))
        return

    transport = server.get("transport", "stdio")
    if transport not in VALID_TRANSPORTS:
        issues.append(
            issue(
                "error",
                f"{where}.transport",
                f"unsupported transport {transport!r}; expected one of {sorted(VALID_TRANSPORTS)}.",
            )
        )
        return

    if transport == "stdio":
        command = server.get("command")
        args = server.get("args", [])
        if not command and not args:
            issues.append(issue("error", where, "stdio transport requires command and/or args."))
        if command is not None and not isinstance(command, str):
            issues.append(issue("error", f"{where}.command", "command must be a string."))
        if not isinstance(args, list):
            issues.append(issue("error", f"{where}.args", "args must be a list."))
        if check_executables and isinstance(command, str) and command:
            executable = command if os.path.sep in command else shutil.which(command)
            if executable is None:
                issues.append(
                    issue(
                        "error",
                        f"{where}.command",
                        f"stdio command {command!r} was not found on PATH.",
                    )
                )
    elif transport in {"sse", "streamable_http"}:
        validate_url_scheme(server.get("url"), {"http", "https"}, f"{where}.url", issues)
    elif transport == "websocket":
        validate_url_scheme(server.get("url"), {"ws", "wss"}, f"{where}.url", issues)

    validate_headers(server.get("headers"), f"{where}.headers", issues)
    validate_roots(server.get("roots"), f"{where}.roots", issues)

    allowed_tools = server.get("allowed_tools")
    if allowed_tools is not None and not isinstance(allowed_tools, list):
        issues.append(issue("error", f"{where}.allowed_tools", "allowed_tools must be a list in YAML/JSON."))

    auth = server.get("auth")
    if auth is not None:
        if not isinstance(auth, dict):
            issues.append(issue("error", f"{where}.auth", "auth must be a mapping."))
        else:
            validate_oauth(auth.get("oauth"), f"{where}.auth.oauth", issues)


def validate_global_oauth(config: dict[str, Any], issues: list[dict[str, str]]) -> None:
    oauth = config.get("oauth")
    if oauth is None:
        return
    if not isinstance(oauth, dict):
        issues.append(issue("error", "oauth", "oauth must be a mapping."))
        return
    token_store = oauth.get("token_store") or {}
    if token_store and not isinstance(token_store, dict):
        issues.append(issue("error", "oauth.token_store", "token_store must be a mapping."))
        return
    if token_store.get("backend") == "redis" and not token_store.get("redis_url"):
        issues.append(issue("warning", "oauth.token_store.redis_url", "redis backend should set redis_url."))


def validate_strict_package_model(config: dict[str, Any], issues: list[dict[str, str]]) -> None:
    try:
        from mcp_agent.config import Settings  # type: ignore
    except Exception as exc:
        issues.append(
            issue(
                "error",
                "mcp_agent.config.Settings",
                f"could not import mcp-agent settings model: {exc}",
            )
        )
        return
    try:
        Settings(**config)
    except Exception as exc:
        issues.append(issue("error", "mcp_agent.config.Settings", str(exc)))


def collect_issues(args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, str]]]:
    config_path = Path(args.config)
    config = load_document(config_path)
    issues: list[dict[str, str]] = []

    mcp = config.get("mcp") or {}
    if not isinstance(mcp, dict):
        issues.append(issue("error", "mcp", "mcp must be a mapping."))
        servers: dict[str, Any] = {}
    else:
        servers = mcp.get("servers") or {}
        if not isinstance(servers, dict):
            issues.append(issue("error", "mcp.servers", "servers must be a mapping."))
            servers = {}

    for expected in args.expect_server:
        if expected not in servers:
            issues.append(issue("error", f"mcp.servers.{expected}", "expected server is missing."))

    for server_name, server_config in servers.items():
        validate_server(
            str(server_name),
            server_config,
            check_executables=args.check_executables,
            issues=issues,
        )

    validate_global_oauth(config, issues)

    if args.strict_package_model:
        validate_strict_package_model(config, issues)

    summary = {
        "ok": not any(item["severity"] == "error" for item in issues),
        "server_count": len(servers),
        "servers": sorted(str(name) for name in servers),
        "errors": sum(1 for item in issues if item["severity"] == "error"),
        "warnings": sum(1 for item in issues if item["severity"] == "warning"),
    }
    return summary, issues


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        summary, issues = collect_issues(args)
    except Exception as exc:
        if args.json:
            print(json.dumps({"ok": False, "errors": 1, "issues": [issue("error", "config", str(exc))]}, indent=2))
        else:
            print(f"ERROR config: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"summary": summary, "issues": issues}, indent=2, sort_keys=True))
    else:
        status = "OK" if summary["ok"] else "FAILED"
        print(f"{status}: {summary['server_count']} server(s), {summary['errors']} error(s), {summary['warnings']} warning(s)")
        for item in issues:
            print(f"{item['severity'].upper()} {item['where']}: {item['message']}")

    if summary["errors"]:
        return 1
    if args.fail_on_warnings and summary["warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
