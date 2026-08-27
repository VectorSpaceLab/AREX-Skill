#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping, Sequence

JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
Format = Literal["auto", "openai-tools", "mcp-server"]


@dataclass(frozen=True, slots=True)
class Finding:
    level: Literal["error", "warning"]
    path: str
    message: str


def load_json(path: Path) -> tuple[JsonValue | None, tuple[Finding, ...]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), ()
    except FileNotFoundError:
        return None, (Finding("error", str(path), "file does not exist"),)
    except json.JSONDecodeError as exc:
        return None, (Finding("error", str(path), f"invalid JSON: {exc}"),)


def as_mapping(value: JsonValue) -> Mapping[str, JsonValue] | None:
    return value if isinstance(value, dict) else None


def as_sequence(value: JsonValue) -> Sequence[JsonValue] | None:
    return value if isinstance(value, list) else None


def is_non_empty_string(value: JsonValue) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_schema(schema: JsonValue, path: str) -> tuple[Finding, ...]:
    mapping = as_mapping(schema)
    if mapping is None:
        return (Finding("error", path, "parameters/inputSchema must be an object"),)

    findings: tuple[Finding, ...] = ()
    schema_type = mapping.get("type")
    properties = mapping.get("properties")
    required = mapping.get("required")

    if schema_type != "object":
        findings += (Finding("warning", f"{path}.type", "OpenAI-compatible tools should use type 'object'"),)
    if properties is not None and not isinstance(properties, dict):
        findings += (Finding("error", f"{path}.properties", "properties must be an object when present"),)
    if required is not None:
        required_items = as_sequence(required)
        if required_items is None or not all(isinstance(item, str) for item in required_items):
            findings += (Finding("error", f"{path}.required", "required must be an array of strings when present"),)
    return findings


def validate_openai_tool(tool: JsonValue, index: int) -> tuple[Finding, ...]:
    path = f"tools[{index}]"
    mapping = as_mapping(tool)
    if mapping is None:
        return (Finding("error", path, "tool must be an object"),)

    findings: tuple[Finding, ...] = ()
    tool_type = mapping.get("type")
    function = as_mapping(mapping.get("function"))

    if tool_type != "function":
        findings += (Finding("error", f"{path}.type", "OpenAI chat tools must have type 'function'"),)
    if function is None:
        return findings + (Finding("error", f"{path}.function", "function object is required"),)
    if not is_non_empty_string(function.get("name")):
        findings += (Finding("error", f"{path}.function.name", "function name is required"),)
    if "description" in function and not isinstance(function.get("description"), str):
        findings += (Finding("warning", f"{path}.function.description", "description should be a string"),)
    findings += validate_schema(function.get("parameters", {}), f"{path}.function.parameters")
    return findings


def validate_responses_tool(tool: JsonValue, index: int) -> tuple[Finding, ...]:
    path = f"tools[{index}]"
    mapping = as_mapping(tool)
    if mapping is None:
        return (Finding("error", path, "tool must be an object"),)

    findings: tuple[Finding, ...] = ()
    if mapping.get("type") != "function":
        findings += (Finding("error", f"{path}.type", "OpenAI Responses tools must have type 'function'"),)
    if not is_non_empty_string(mapping.get("name")):
        findings += (Finding("error", f"{path}.name", "tool name is required"),)
    if "description" in mapping and not isinstance(mapping.get("description"), str):
        findings += (Finding("warning", f"{path}.description", "description should be a string"),)
    findings += validate_schema(mapping.get("parameters", {}), f"{path}.parameters")
    return findings


def validate_openai_tools(data: JsonValue) -> tuple[Finding, ...]:
    tools = data
    if isinstance(data, dict):
        tools = data.get("tools")
    sequence = as_sequence(tools)
    if sequence is None:
        return (Finding("error", "tools", "expected an array or an object with a tools array"),)
    if not sequence:
        return (Finding("warning", "tools", "tools array is empty"),)

    findings: tuple[Finding, ...] = ()
    for index, tool in enumerate(sequence):
        mapping = as_mapping(tool)
        if mapping is not None and "function" in mapping:
            findings += validate_openai_tool(tool, index)
        else:
            findings += validate_responses_tool(tool, index)
    return findings


def validate_mcp_tool(tool: JsonValue, index: int) -> tuple[Finding, ...]:
    path = f"tools[{index}]"
    mapping = as_mapping(tool)
    if mapping is None:
        return (Finding("error", path, "MCP tool must be an object"),)

    findings: tuple[Finding, ...] = ()
    if not is_non_empty_string(mapping.get("name")):
        findings += (Finding("error", f"{path}.name", "MCP tool name is required"),)
    if "description" in mapping and mapping.get("description") is not None and not isinstance(mapping.get("description"), str):
        findings += (Finding("warning", f"{path}.description", "description should be a string"),)
    schema = mapping.get("inputSchema") or mapping.get("input_schema") or {}
    findings += validate_schema(schema, f"{path}.inputSchema")
    return findings


def validate_mcp_server(data: JsonValue) -> tuple[Finding, ...]:
    mapping = as_mapping(data)
    if mapping is None:
        return (Finding("error", "$", "MCP server metadata must be an object"),)

    findings: tuple[Finding, ...] = ()
    server_label = mapping.get("name") or mapping.get("server_name") or mapping.get("alias") or mapping.get("server_id")
    if not is_non_empty_string(server_label):
        findings += (Finding("warning", "$", "server metadata should include name, server_name, alias, or server_id"),)

    transport = mapping.get("transport")
    if transport is not None and transport not in ("http", "sse", "stdio"):
        findings += (Finding("error", "transport", "transport must be one of http, sse, stdio"),)
    if transport in ("http", "sse") and not is_non_empty_string(mapping.get("url")):
        findings += (Finding("warning", "url", "HTTP/SSE MCP servers should include a URL"),)
    if transport == "stdio" and not is_non_empty_string(mapping.get("command")):
        findings += (Finding("warning", "command", "stdio MCP servers should include a command"),)

    auth_type = mapping.get("auth_type")
    valid_auth = {None, "none", "api_key", "bearer_token", "basic", "authorization", "oauth2", "aws_sigv4", "token", "oauth2_token_exchange"}
    if auth_type not in valid_auth:
        findings += (Finding("error", "auth_type", "unsupported MCP auth_type"),)
    if mapping.get("oauth2_flow") not in (None, "client_credentials", "authorization_code"):
        findings += (Finding("error", "oauth2_flow", "oauth2_flow must be client_credentials or authorization_code"),)
    if mapping.get("delegate_auth_to_upstream") is True and auth_type != "oauth2":
        findings += (Finding("warning", "delegate_auth_to_upstream", "only applies to auth_type oauth2"),)
    if mapping.get("oauth_passthrough") is True and auth_type not in (None, "none"):
        findings += (Finding("warning", "oauth_passthrough", "only applies when auth_type is none or absent"),)

    tools_value = mapping.get("tools")
    tools = as_sequence(tools_value) if tools_value is not None else ()
    if tools_value is not None and tools is None:
        findings += (Finding("error", "tools", "tools must be an array when present"),)
    if tools:
        for index, tool in enumerate(tools):
            findings += validate_mcp_tool(tool, index)
    return findings


def infer_format(data: JsonValue) -> Format:
    if isinstance(data, list):
        return "openai-tools"
    if isinstance(data, dict) and isinstance(data.get("tools"), list):
        tools = data.get("tools")
        if tools and isinstance(tools[0], dict) and ("function" in tools[0] or tools[0].get("type") == "function"):
            return "openai-tools"
        return "mcp-server"
    if isinstance(data, dict) and any(key in data for key in ("transport", "server_name", "server_id", "alias")):
        return "mcp-server"
    return "openai-tools"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate OpenAI tool JSON or MCP server metadata without network calls.")
    parser.add_argument("json_file", type=Path, help="Path to a JSON file containing tools or MCP server metadata.")
    parser.add_argument("--format", choices=("auto", "openai-tools", "mcp-server"), default="auto", help="Input shape to validate. Defaults to auto detection.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    data, load_findings = load_json(args.json_file)
    if load_findings:
        print_findings(load_findings)
        return 1
    selected_format = infer_format(data) if args.format == "auto" else args.format
    findings = validate_mcp_server(data) if selected_format == "mcp-server" else validate_openai_tools(data)
    print(f"format={selected_format}")
    print_findings(findings)
    has_errors = any(finding.level == "error" for finding in findings)
    has_warnings = any(finding.level == "warning" for finding in findings)
    if has_errors or (args.strict and has_warnings):
        return 1
    print("ok")
    return 0


def print_findings(findings: Sequence[Finding]) -> None:
    for finding in findings:
        print(f"{finding.level}: {finding.path}: {finding.message}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
