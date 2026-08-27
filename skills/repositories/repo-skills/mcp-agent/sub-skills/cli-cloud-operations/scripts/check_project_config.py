#!/usr/bin/env python3
"""Read-only mcp-agent project configuration checker.

The checker mirrors the CLI's config discovery rules closely enough for
troubleshooting, validates YAML syntax when PyYAML is available, summarizes
deployment-relevant fields, and reports likely CI/deploy issues. It never
imports user application code, contacts Cloud APIs, reads secret values into
output, or writes files.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

try:  # Prefer the same parser family used by mcp-agent when available.
    import yaml as _yaml  # type: ignore
except Exception:  # pragma: no cover - environment dependent
    _yaml = None

CONFIG_NAMES = ("mcp-agent.config.yaml", "mcp_agent.config.yaml")
SECRETS_NAMES = ("mcp-agent.secrets.yaml", "mcp_agent.secrets.yaml")
RISKY_IGNORE_GLOBS = (
    ".env",
    ".env.*",
    ".venv/",
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    "*.log",
)


@dataclass
class FileStatus:
    path: str | None
    exists: bool
    valid_yaml: bool | None = None
    error: str | None = None
    parser: str | None = None
    top_level_keys: list[str] = field(default_factory=list)


@dataclass
class CheckResult:
    ok: bool
    project: str
    config: FileStatus
    secrets: FileStatus
    discovered_config_candidates: list[str]
    discovered_secrets_candidates: list[str]
    preload_active: bool
    app_name: str | None
    execution_engine: str | None
    mcp_servers: list[dict[str, Any]]
    env_specs: list[dict[str, Any]]
    missing_env_values: list[str]
    ignore_file: str | None
    ignore_warnings: list[str]
    warnings: list[str]


def upward_dirs(start: Path) -> list[Path]:
    dirs: list[Path] = []
    current = start.resolve()
    while True:
        dirs.append(current)
        if current == current.parent:
            break
        current = current.parent
    return dirs


def find_named_file(start: Path, names: tuple[str, ...]) -> Path | None:
    for directory in upward_dirs(start):
        for name in names:
            direct = directory / name
            if direct.exists():
                return direct
            nested = directory / ".mcp-agent" / name
            if nested.exists():
                return nested
    home = Path.home() / ".mcp-agent"
    for name in names:
        candidate = home / name
        if candidate.exists():
            return candidate
    return None


def collect_candidates(start: Path, names: tuple[str, ...]) -> list[str]:
    candidates: list[str] = []
    for directory in upward_dirs(start):
        for name in names:
            for candidate in (directory / name, directory / ".mcp-agent" / name):
                if candidate.exists():
                    candidates.append(str(candidate))
    home = Path.home() / ".mcp-agent"
    for name in names:
        candidate = home / name
        if candidate.exists():
            candidates.append(str(candidate))
    return candidates


def strip_comment(line: str) -> str:
    """Remove simple YAML comments outside single/double quotes."""
    in_single = False
    in_double = False
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_double:
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            if index == 0 or line[index - 1].isspace():
                return line[:index].rstrip()
    return line.rstrip()


def parse_scalar(raw: str) -> Any:
    value = strip_comment(raw).strip()
    if value in {"", "null", "Null", "NULL", "~"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if re.fullmatch(r"-?\d+", value):
        try:
            return int(value)
        except ValueError:
            return value
    if re.fullmatch(r"-?\d+\.\d+", value):
        try:
            return float(value)
        except ValueError:
            return value
    return value


def split_key_value(stripped: str) -> tuple[str, str] | None:
    if ":" not in stripped:
        return None
    key, value = stripped.split(":", 1)
    key = key.strip().strip('"\'')
    if not key:
        return None
    return key, value.strip()


def line_records(text: str) -> list[tuple[int, str]]:
    records: list[tuple[int, str]] = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = strip_comment(raw.strip())
        if stripped:
            records.append((indent, stripped))
    return records


def find_block(records: list[tuple[int, str]], key: str, parent_index: int = -1) -> tuple[int, int, int] | None:
    start = parent_index + 1
    parent_indent = records[parent_index][0] if parent_index >= 0 else -1
    for index in range(start, len(records)):
        indent, stripped = records[index]
        if parent_index >= 0 and indent <= parent_indent:
            return None
        pair = split_key_value(stripped)
        if pair and pair[0] == key:
            end = len(records)
            for cursor in range(index + 1, len(records)):
                next_indent = records[cursor][0]
                if next_indent <= indent:
                    end = cursor
                    break
            return index, end, indent
    return None


def parse_inline_mapping(value: str) -> dict[str, Any] | None:
    stripped = value.strip()
    if not (stripped.startswith("{") and stripped.endswith("}")):
        return None
    body = stripped[1:-1].strip()
    if not body or ":" not in body:
        return None
    key, raw = body.split(":", 1)
    return {key.strip().strip('"\''): parse_scalar(raw)}


def parse_env_from_records(records: list[tuple[int, str]]) -> list[Any]:
    block = find_block(records, "env")
    if not block:
        return []
    index, end, indent = block
    _, line = records[index]
    pair = split_key_value(line)
    if pair and pair[1].strip() in {"[]", ""}:
        values: list[Any] = []
    else:
        return []
    for cursor in range(index + 1, end):
        item_indent, stripped = records[cursor]
        if item_indent <= indent or not stripped.startswith("- "):
            continue
        raw_item = stripped[2:].strip()
        inline = parse_inline_mapping(raw_item)
        if inline is not None:
            values.append(inline)
            continue
        pair = split_key_value(raw_item)
        if pair and pair[1] != "":
            values.append({pair[0]: parse_scalar(pair[1])})
        else:
            values.append(parse_scalar(raw_item))
    return values


def parse_servers_from_records(records: list[tuple[int, str]]) -> dict[str, dict[str, Any]]:
    mcp_block = find_block(records, "mcp")
    if not mcp_block:
        return {}
    mcp_index, mcp_end, _ = mcp_block
    servers_block = find_block(records[:mcp_end], "servers", parent_index=mcp_index)
    if not servers_block:
        return {}
    servers_index, servers_end, servers_indent = servers_block
    servers: dict[str, dict[str, Any]] = {}
    current_name: str | None = None
    current_indent: int | None = None
    for cursor in range(servers_index + 1, servers_end):
        indent, stripped = records[cursor]
        if indent <= servers_indent:
            break
        pair = split_key_value(stripped)
        if not pair:
            continue
        key, raw_value = pair
        if indent == servers_indent + 2:
            current_name = key
            current_indent = indent
            servers[current_name] = {}
            if raw_value:
                parsed = parse_inline_mapping(raw_value)
                if parsed:
                    servers[current_name].update(parsed)
            continue
        if current_name and current_indent is not None and indent > current_indent:
            servers[current_name][key] = parse_scalar(raw_value)
    return servers


def minimal_yaml_parse(text: str) -> dict[str, Any]:
    """Best-effort parser for common mcp-agent config shapes.

    This is not a general YAML parser. It exists so the checker can still report
    discovery and simple deployment hints when PyYAML is unavailable.
    """
    records = line_records(text)
    data: dict[str, Any] = {}
    for indent, stripped in records:
        if indent != 0:
            continue
        pair = split_key_value(stripped)
        if not pair:
            continue
        key, raw_value = pair
        data[key] = parse_scalar(raw_value) if raw_value else {}
    env = parse_env_from_records(records)
    if env:
        data["env"] = env
    servers = parse_servers_from_records(records)
    if servers:
        data.setdefault("mcp", {})
        if isinstance(data["mcp"], dict):
            data["mcp"].setdefault("servers", servers)
    return data


def load_yaml_status(path: Path | None, redact_values: bool = False) -> tuple[FileStatus, Any]:
    if path is None:
        return FileStatus(path=None, exists=False), None
    status = FileStatus(path=str(path), exists=path.exists())
    if not path.exists():
        return status, None
    try:
        text = path.read_text(encoding="utf-8")
        if _yaml is not None:
            data = _yaml.safe_load(text) or {}
            status.valid_yaml = True
            status.parser = "pyyaml"
        else:
            data = minimal_yaml_parse(text)
            status.valid_yaml = None
            status.parser = "lightweight"
            status.error = "PyYAML unavailable; used lightweight parser for common config fields."
        if isinstance(data, dict):
            status.top_level_keys = sorted(str(key) for key in data.keys())
        if redact_values and isinstance(data, dict):
            data = redact_tree(data)
        return status, data
    except Exception as exc:
        status.valid_yaml = False
        status.error = str(exc)
        status.parser = "pyyaml" if _yaml is not None else "lightweight"
        return status, None


def redact_tree(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): redact_tree(child) for key, child in value.items()}
    if isinstance(value, list):
        return [redact_tree(item) for item in value]
    if value in (None, ""):
        return value
    return "<redacted>"


def summarize_servers(config_data: Any) -> list[dict[str, Any]]:
    if not isinstance(config_data, dict):
        return []
    mcp_section = config_data.get("mcp") if isinstance(config_data.get("mcp"), dict) else {}
    servers = (mcp_section or {}).get("servers") or {}
    if not isinstance(servers, dict):
        return []
    summary: list[dict[str, Any]] = []
    for name, settings in sorted(servers.items()):
        settings = settings or {}
        if not isinstance(settings, dict):
            summary.append({"name": str(name), "status": "invalid", "reason": "server entry is not a mapping"})
            continue
        transport = str(settings.get("transport") or "stdio")
        command = settings.get("command")
        url = settings.get("url")
        warnings: list[str] = []
        if transport == "stdio" and not command:
            warnings.append("stdio transport needs command")
        if transport in {"http", "sse", "streamable_http", "websocket"} and not url:
            warnings.append(f"{transport} transport needs url")
        summary.append(
            {
                "name": str(name),
                "transport": transport,
                "has_command": bool(command),
                "has_url": bool(url),
                "warnings": warnings,
            }
        )
    return summary


def normalize_env_specs(config_data: Any) -> list[dict[str, Any]]:
    if not isinstance(config_data, dict):
        return []
    env_section = config_data.get("env") or []
    if not isinstance(env_section, list):
        return [{"key": None, "valid": False, "reason": "env must be a list"}]
    specs: list[dict[str, Any]] = []
    for item in env_section:
        if isinstance(item, str):
            specs.append({"key": item, "fallback": None, "valid": bool(item.strip())})
        elif isinstance(item, dict) and len(item) == 1:
            key, fallback = next(iter(item.items()))
            specs.append({"key": str(key), "fallback": fallback, "valid": bool(str(key).strip())})
        else:
            specs.append({"key": None, "fallback": None, "valid": False, "reason": "env entries must be strings or single-key mappings"})
    return specs


def missing_env_values(specs: list[dict[str, Any]]) -> list[str]:
    missing: list[str] = []
    for spec in specs:
        key = spec.get("key")
        if not key or not spec.get("valid", True):
            continue
        fallback = spec.get("fallback")
        if os.environ.get(str(key)) is None and fallback in (None, ""):
            missing.append(str(key))
    return missing


def resolve_ignore_file(config_path: Path | None, project: Path, explicit: Path | None) -> Path | None:
    if explicit:
        return explicit
    if config_path:
        candidate = config_path.parent / ".mcpacignore"
        if candidate.exists():
            return candidate
    candidate = project / ".mcpacignore"
    if candidate.exists():
        return candidate
    return None


def inspect_ignore(ignore_file: Path | None) -> list[str]:
    warnings: list[str] = []
    if ignore_file is None or not ignore_file.exists():
        return ["No .mcpacignore or explicit ignore file found; deploy will use default excludes only."]
    text = ignore_file.read_text(encoding="utf-8", errors="replace")
    for pattern in RISKY_IGNORE_GLOBS:
        if pattern not in text:
            warnings.append(f"Consider excluding {pattern}")
    return warnings


def build_result(args: argparse.Namespace) -> CheckResult:
    project = args.project.resolve()
    config_path = args.config.resolve() if args.config else find_named_file(project, CONFIG_NAMES)
    secrets_path = args.secrets.resolve() if args.secrets else None
    if secrets_path is None and config_path is not None:
        for name in SECRETS_NAMES:
            candidate = config_path.parent / name
            if candidate.exists():
                secrets_path = candidate
                break
    if secrets_path is None:
        secrets_path = find_named_file(project, SECRETS_NAMES)

    config_status, config_data = load_yaml_status(config_path)
    secrets_status, _ = load_yaml_status(secrets_path, redact_values=True)

    servers = summarize_servers(config_data)
    specs = normalize_env_specs(config_data)
    missing = missing_env_values(specs)
    explicit_ignore = args.ignore_file.resolve() if args.ignore_file else None
    ignore_path = resolve_ignore_file(config_path, project, explicit_ignore)

    warnings: list[str] = []
    if _yaml is None:
        warnings.append("PyYAML is unavailable; YAML syntax validation is partial and uses a lightweight parser.")
    if os.environ.get("MCP_APP_SETTINGS_PRELOAD"):
        warnings.append("MCP_APP_SETTINGS_PRELOAD is set and can override file-based settings discovery.")
    if not config_status.exists:
        warnings.append("No mcp-agent config file discovered.")
    if config_status.valid_yaml is False:
        warnings.append("Config file is not valid YAML.")
    if secrets_status.exists and secrets_status.valid_yaml is False:
        warnings.append("Secrets file is not valid YAML.")
    for server in servers:
        warnings.extend(f"Server {server.get('name')}: {warning}" for warning in server.get("warnings", []))
    if missing:
        warnings.append("Deploy --non-interactive will fail unless missing env values are exported or given fallbacks.")

    app_name = None
    execution_engine = None
    if isinstance(config_data, dict):
        app_name = config_data.get("name")
        execution_engine = config_data.get("execution_engine")

    ok = bool(config_status.exists and config_status.valid_yaml is not False and not missing)
    return CheckResult(
        ok=ok,
        project=str(project),
        config=config_status,
        secrets=secrets_status,
        discovered_config_candidates=collect_candidates(project, CONFIG_NAMES),
        discovered_secrets_candidates=collect_candidates(project, SECRETS_NAMES),
        preload_active=bool(os.environ.get("MCP_APP_SETTINGS_PRELOAD")),
        app_name=app_name,
        execution_engine=execution_engine,
        mcp_servers=servers,
        env_specs=specs,
        missing_env_values=missing,
        ignore_file=str(ignore_path) if ignore_path else None,
        ignore_warnings=inspect_ignore(ignore_path),
        warnings=warnings,
    )


def render_text(result: CheckResult) -> str:
    lines = [
        f"Project: {result.project}",
        f"OK: {result.ok}",
        f"Config: {result.config.path or 'not found'}",
        f"Config parser: {result.config.parser or '-'}",
        f"Secrets: {result.secrets.path or 'not found'}",
        f"Preload active: {result.preload_active}",
        f"App name: {result.app_name or '-'}",
        f"Execution engine: {result.execution_engine or 'asyncio/default'}",
        f"Ignore file: {result.ignore_file or 'not found'}",
        "",
        "MCP servers:",
    ]
    if result.mcp_servers:
        for server in result.mcp_servers:
            warning_text = "; ".join(server.get("warnings") or [])
            lines.append(
                f"- {server.get('name')} ({server.get('transport')}): "
                f"command={server.get('has_command')} url={server.get('has_url')}"
                + (f" [{warning_text}]" if warning_text else "")
            )
    else:
        lines.append("- none")

    lines.append("")
    lines.append("Deployment env specs:")
    if result.env_specs:
        for spec in result.env_specs:
            if spec.get("key"):
                status = "set" if os.environ.get(str(spec["key"])) is not None else "missing"
                fallback = "fallback" if spec.get("fallback") not in (None, "") else "no fallback"
                lines.append(f"- {spec['key']}: {status}, {fallback}")
            else:
                lines.append(f"- invalid: {spec.get('reason')}")
    else:
        lines.append("- none")

    if result.warnings or result.ignore_warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in result.warnings + result.ignore_warnings:
            lines.append(f"- {warning}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="Project directory to inspect.")
    parser.add_argument("--config", type=Path, help="Explicit config file path.")
    parser.add_argument("--secrets", type=Path, help="Explicit secrets file path.")
    parser.add_argument("--ignore-file", type=Path, help="Explicit deploy ignore file path.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args()

    result = build_result(args)
    if args.json:
        print(json.dumps(asdict(result), indent=2, sort_keys=True))
    else:
        print(render_text(result), end="")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
