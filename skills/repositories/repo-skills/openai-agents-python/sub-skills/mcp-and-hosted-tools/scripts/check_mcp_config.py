#!/usr/bin/env python3
"""Validate an OpenAI Agents Python MCP config without starting servers.

The helper checks JSON shape, imports the MCP SDK surfaces, validates common
local/hosted MCP fields, and optionally reports stdio command discovery. It does
not connect to HTTP endpoints or launch stdio commands.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SUPPORTED_TYPES = {"stdio", "streamable_http", "sse", "hosted"}
LOCAL_TYPES = {"stdio", "streamable_http", "sse"}
APPROVAL_POLICIES = {"always", "never"}


@dataclass
class Finding:
    level: str
    message: str
    path: str = "$"

    def to_dict(self) -> dict[str, str]:
        return {"level": self.level, "path": self.path, "message": self.message}


@dataclass
class CommandInfo:
    path: str
    command: str
    found: bool
    resolved: str | None
    args: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "command": self.command,
            "found": self.found,
            "resolved": self.resolved,
            "args": self.args,
        }


def load_json(path: Path) -> Any:
    if str(path) == "-":
        return json.load(sys.stdin)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def import_mcp_surfaces() -> tuple[bool, str | None]:
    try:
        from agents import HostedMCPTool  # noqa: F401
        from agents.mcp import (  # noqa: F401
            MCPServerSse,
            MCPServerStdio,
            MCPServerStreamableHttp,
            create_static_tool_filter,
        )
    except Exception as exc:  # pragma: no cover - exercised in broken envs.
        return False, f"{type(exc).__name__}: {exc}"
    return True, None


def as_servers(config: Any, findings: list[Finding]) -> list[Any]:
    if isinstance(config, list):
        return config
    if isinstance(config, dict):
        for key in ("servers", "mcp_servers", "tools"):
            value = config.get(key)
            if isinstance(value, list):
                return value
        if "type" in config:
            return [config]
        findings.append(
            Finding(
                "error",
                "config object must include a servers/mcp_servers/tools list or a single server type",
            )
        )
        return []
    findings.append(Finding("error", "config must be a JSON object or array"))
    return []


def is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def validate_approval(value: Any, path: str, findings: list[Finding]) -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, str):
        if value not in APPROVAL_POLICIES:
            findings.append(Finding("error", "approval policy must be 'always' or 'never'", path))
        return
    if not isinstance(value, dict):
        findings.append(Finding("error", "approval policy must be a string, boolean, object, or null", path))
        return

    looks_grouped = any(
        key in value and isinstance(value.get(key), dict) and "tool_names" in value.get(key, {})
        for key in APPROVAL_POLICIES
    )
    if looks_grouped:
        unexpected = sorted(set(value) - APPROVAL_POLICIES)
        if unexpected:
            findings.append(Finding("error", f"unexpected grouped approval keys: {unexpected}", path))
        always_names = value.get("always", {}).get("tool_names", []) if isinstance(value.get("always", {}), dict) else []
        never_names = value.get("never", {}).get("tool_names", []) if isinstance(value.get("never", {}), dict) else []
        for policy, names in (("always", always_names), ("never", never_names)):
            if not is_string_list(names):
                findings.append(Finding("error", "tool_names must be a list of strings", f"{path}.{policy}.tool_names"))
        if is_string_list(always_names) and is_string_list(never_names):
            overlap = sorted(set(always_names) & set(never_names))
            if overlap:
                findings.append(Finding("error", f"tool names appear in both always and never: {overlap}", path))
        return

    for tool_name, policy in value.items():
        if not isinstance(tool_name, str):
            findings.append(Finding("error", "approval mapping keys must be tool-name strings", path))
        if isinstance(policy, bool):
            continue
        if policy not in APPROVAL_POLICIES:
            findings.append(Finding("error", "approval mapping values must be 'always', 'never', or boolean", f"{path}.{tool_name}"))


def validate_tool_filter(value: Any, path: str, findings: list[Finding]) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        findings.append(Finding("warning", "only static JSON tool_filter objects can be validated by this helper", path))
        return
    allowed_keys = {"allowed_tool_names", "blocked_tool_names"}
    unexpected = sorted(set(value) - allowed_keys)
    if unexpected:
        findings.append(Finding("warning", f"unexpected static tool_filter keys: {unexpected}", path))
    for key in allowed_keys:
        if key in value and not is_string_list(value[key]):
            findings.append(Finding("error", f"{key} must be a list of strings", f"{path}.{key}"))


def validate_common_local(server: dict[str, Any], path: str, findings: list[Finding]) -> None:
    for bool_key in ("cache_tools_list", "use_structured_content"):
        if bool_key in server and not isinstance(server[bool_key], bool):
            findings.append(Finding("error", f"{bool_key} must be boolean", f"{path}.{bool_key}"))
    if "max_retry_attempts" in server and not isinstance(server["max_retry_attempts"], int):
        findings.append(Finding("error", "max_retry_attempts must be integer", f"{path}.max_retry_attempts"))
    if "retry_backoff_seconds_base" in server and not isinstance(
        server["retry_backoff_seconds_base"], (int, float)
    ):
        findings.append(
            Finding("error", "retry_backoff_seconds_base must be numeric", f"{path}.retry_backoff_seconds_base")
        )
    if "client_session_timeout_seconds" in server and not isinstance(
        server["client_session_timeout_seconds"], (int, float, type(None))
    ):
        findings.append(
            Finding("error", "client_session_timeout_seconds must be numeric or null", f"{path}.client_session_timeout_seconds")
        )
    validate_approval(server.get("require_approval"), f"{path}.require_approval", findings)
    validate_tool_filter(server.get("tool_filter"), f"{path}.tool_filter", findings)


def validate_params_object(server: dict[str, Any], path: str, findings: list[Finding]) -> dict[str, Any]:
    params = server.get("params")
    if params is None:
        params = {key: server[key] for key in ("command", "args", "env", "cwd", "url", "headers") if key in server}
    if not isinstance(params, dict):
        findings.append(Finding("error", "params must be an object", f"{path}.params"))
        return {}
    return params


def validate_stdio(server: dict[str, Any], path: str, findings: list[Finding], commands: list[CommandInfo]) -> None:
    validate_common_local(server, path, findings)
    params = validate_params_object(server, path, findings)
    command = params.get("command")
    if not isinstance(command, str) or not command:
        findings.append(Finding("error", "stdio params.command is required and must be a non-empty string", f"{path}.params.command"))
        return
    args = params.get("args", [])
    if not is_string_list(args):
        findings.append(Finding("error", "stdio params.args must be a list of strings", f"{path}.params.args"))
        args = []
    if "env" in params and not isinstance(params["env"], dict):
        findings.append(Finding("error", "stdio params.env must be an object", f"{path}.params.env"))
    if "cwd" in params and not isinstance(params["cwd"], str):
        findings.append(Finding("error", "stdio params.cwd must be a string", f"{path}.params.cwd"))
    resolved = shutil.which(command)
    commands.append(CommandInfo(path=f"{path}.params.command", command=command, found=resolved is not None, resolved=resolved, args=args))
    if resolved is None:
        findings.append(Finding("warning", f"stdio command is not currently on PATH: {command}", f"{path}.params.command"))


def validate_http(server: dict[str, Any], path: str, findings: list[Finding], transport: str) -> None:
    validate_common_local(server, path, findings)
    params = validate_params_object(server, path, findings)
    url = params.get("url")
    if not isinstance(url, str) or not url:
        findings.append(Finding("error", f"{transport} params.url is required and must be a non-empty string", f"{path}.params.url"))
    elif not url.startswith(("http://", "https://")):
        findings.append(Finding("warning", f"{transport} URL should usually start with http:// or https://", f"{path}.params.url"))
    if "headers" in params and not isinstance(params["headers"], dict):
        findings.append(Finding("error", f"{transport} params.headers must be an object", f"{path}.params.headers"))
    for numeric_key in ("timeout", "sse_read_timeout"):
        if numeric_key in params and not isinstance(params[numeric_key], (int, float)):
            findings.append(Finding("error", f"{transport} params.{numeric_key} must be numeric", f"{path}.params.{numeric_key}"))
    if transport == "streamable_http" and "terminate_on_close" in params and not isinstance(params["terminate_on_close"], bool):
        findings.append(Finding("error", "streamable_http params.terminate_on_close must be boolean", f"{path}.params.terminate_on_close"))


def validate_hosted(server: dict[str, Any], path: str, findings: list[Finding]) -> None:
    tool_config = server.get("tool_config", server)
    if not isinstance(tool_config, dict):
        findings.append(Finding("error", "hosted tool_config must be an object", f"{path}.tool_config"))
        return
    if tool_config.get("type") != "mcp":
        findings.append(Finding("error", "hosted MCP tool_config.type must be 'mcp'", f"{path}.tool_config.type"))
    label = tool_config.get("server_label")
    if not isinstance(label, str) or not label:
        findings.append(Finding("error", "hosted MCP server_label is required", f"{path}.tool_config.server_label"))
    has_url = isinstance(tool_config.get("server_url"), str) and bool(tool_config.get("server_url"))
    has_connector = isinstance(tool_config.get("connector_id"), str) and bool(tool_config.get("connector_id"))
    if not has_url and not has_connector:
        findings.append(
            Finding("error", "hosted MCP requires server_url or connector_id", f"{path}.tool_config")
        )
    validate_approval(tool_config.get("require_approval"), f"{path}.tool_config.require_approval", findings)
    if "defer_loading" in tool_config and not isinstance(tool_config["defer_loading"], bool):
        findings.append(Finding("error", "defer_loading must be boolean", f"{path}.tool_config.defer_loading"))


def normalize_type(server: dict[str, Any]) -> str | None:
    raw_type = server.get("type") or server.get("transport") or server.get("kind")
    if raw_type == "mcp" or (server.get("tool_config", {}).get("type") == "mcp" if isinstance(server.get("tool_config"), dict) else False):
        return "hosted"
    if isinstance(raw_type, str):
        normalized = raw_type.replace("-", "_").lower()
        aliases = {
            "streamablehttp": "streamable_http",
            "streamable_http": "streamable_http",
            "http": "streamable_http",
            "stdio": "stdio",
            "sse": "sse",
            "hosted_mcp": "hosted",
            "hosted": "hosted",
        }
        return aliases.get(normalized, normalized)
    params = server.get("params") if isinstance(server.get("params"), dict) else server
    if isinstance(params, dict):
        if "command" in params:
            return "stdio"
        if "url" in params:
            return "streamable_http"
    return None


def validate_config(config: Any) -> dict[str, Any]:
    findings: list[Finding] = []
    commands: list[CommandInfo] = []
    imports_ok, import_error = import_mcp_surfaces()
    if not imports_ok:
        findings.append(Finding("error", f"failed to import Agents MCP surfaces: {import_error}"))

    servers = as_servers(config, findings)
    for index, item in enumerate(servers):
        path = f"$.servers[{index}]"
        if not isinstance(item, dict):
            findings.append(Finding("error", "server entry must be an object", path))
            continue
        server_type = normalize_type(item)
        if server_type not in SUPPORTED_TYPES:
            findings.append(
                Finding(
                    "error",
                    f"unsupported or missing server type; expected one of {sorted(SUPPORTED_TYPES)}",
                    f"{path}.type",
                )
            )
            continue
        if server_type == "stdio":
            validate_stdio(item, path, findings, commands)
        elif server_type == "streamable_http":
            validate_http(item, path, findings, "streamable_http")
        elif server_type == "sse":
            validate_http(item, path, findings, "sse")
        elif server_type == "hosted":
            validate_hosted(item, path, findings)

    error_count = sum(1 for finding in findings if finding.level == "error")
    warning_count = sum(1 for finding in findings if finding.level == "warning")
    return {
        "ok": error_count == 0,
        "imports_ok": imports_ok,
        "server_count": len(servers),
        "error_count": error_count,
        "warning_count": warning_count,
        "findings": [finding.to_dict() for finding in findings],
        "commands": [command.to_dict() for command in commands],
    }


def render_text(report: dict[str, Any], *, show_commands: bool) -> str:
    lines = [
        f"MCP config valid: {report['ok']}",
        f"Agents MCP imports: {report['imports_ok']}",
        f"Servers checked: {report['server_count']}",
        f"Errors: {report['error_count']}  Warnings: {report['warning_count']}",
    ]
    if report["findings"]:
        lines.append("")
        lines.append("Findings:")
        for finding in report["findings"]:
            lines.append(f"- {finding['level'].upper()} {finding['path']}: {finding['message']}")
    if show_commands and report["commands"]:
        lines.append("")
        lines.append("Configured stdio commands (not started):")
        for command in report["commands"]:
            status = "found" if command["found"] else "not found"
            resolved = f" -> {command['resolved']}" if command["resolved"] else ""
            args = " ".join(command["args"])
            suffix = f" {args}" if args else ""
            lines.append(f"- {command['path']}: {command['command']}{suffix} ({status}{resolved})")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate an OpenAI Agents Python MCP JSON config without starting servers.",
    )
    parser.add_argument(
        "config",
        type=Path,
        help="Path to a JSON config file, or '-' to read JSON from stdin.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable JSON report.",
    )
    parser.add_argument(
        "--list-commands",
        action="store_true",
        help="Show configured stdio commands and PATH discovery results. Commands are not executed.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = load_json(args.config)
    except json.JSONDecodeError as exc:
        report = {
            "ok": False,
            "imports_ok": None,
            "server_count": 0,
            "error_count": 1,
            "warning_count": 0,
            "findings": [
                {"level": "error", "path": "$", "message": f"invalid JSON: {exc.msg} at line {exc.lineno} column {exc.colno}"}
            ],
            "commands": [],
        }
    except OSError as exc:
        report = {
            "ok": False,
            "imports_ok": None,
            "server_count": 0,
            "error_count": 1,
            "warning_count": 0,
            "findings": [{"level": "error", "path": str(args.config), "message": str(exc)}],
            "commands": [],
        }
    else:
        report = validate_config(config)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report, show_commands=args.list_commands))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
