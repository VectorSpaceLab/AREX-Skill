#!/usr/bin/env python3
"""Read-only validator for Mem0 MCP/editor-plugin configuration files.

The script inspects JSON and TOML-like config files for Mem0 remote MCP
registrations, duplicate entries, auth/header shape, and common Codex hook
feature-flag issues. It never writes files and redacts secret-looking values.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

MEM0_URL_RE = re.compile(r"https://mcp\.mem0\.ai/mcp/?")
SECRET_RE = re.compile(r"(m0-[A-Za-z0-9_\-]{6,}|Token\s+[A-Za-z0-9_\-]{8,}|Bearer\s+[A-Za-z0-9_\-]{8,})")


def redact(value: Any) -> Any:
    if isinstance(value, str):
        return SECRET_RE.sub("<redacted>", value)
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def load_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        print(f"{path}: ERROR invalid JSON: {exc}")
        return None
    except OSError as exc:
        print(f"{path}: ERROR cannot read: {exc}")
        return None


def find_mem0_entries_json(data: Any, prefix: str = "") -> list[tuple[str, dict[str, Any]]]:
    entries: list[tuple[str, dict[str, Any]]] = []
    if isinstance(data, dict):
        for key, value in data.items():
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(value, dict):
                serialized = json.dumps(value, sort_keys=True)
                if key.lower() == "mem0" or "mcp.mem0.ai/mcp" in serialized or "@mem0/opencode-plugin" in serialized:
                    entries.append((next_prefix, value))
                    continue
                entries.extend(find_mem0_entries_json(value, next_prefix))
            elif isinstance(value, list):
                entries.extend(find_mem0_entries_json(value, next_prefix))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            entries.extend(find_mem0_entries_json(value, f"{prefix}[{index}]"))
    return entries


def check_json(path: Path) -> int:
    data = load_json(path)
    if data is None:
        return 1

    issues = 0
    entries = find_mem0_entries_json(data)
    unique_paths = []
    seen = set()
    for entry_path, entry in entries:
        if entry_path not in seen:
            unique_paths.append((entry_path, entry))
            seen.add(entry_path)

    print(f"{path}: JSON parsed")
    if not unique_paths:
        print("  WARN no Mem0 MCP-looking entry found")
        return 0

    print(f"  Mem0-looking entries: {len(unique_paths)}")
    if len(unique_paths) > 1:
        print("  WARN possible duplicate Mem0 registrations; keep only one MCP/plugin path per host")

    for entry_path, entry in unique_paths:
        redacted_entry = redact(entry)
        print(f"  - {entry_path}: {json.dumps(redacted_entry, sort_keys=True)}")
        serialized = json.dumps(entry)
        if "mcp.mem0.ai/mcp" not in serialized and "@mem0/opencode-plugin" not in serialized:
            print("    WARN entry does not reference the Mem0 remote MCP URL or known native plugin")
        if "mcp.mem0.ai/mcp" in serialized and not MEM0_URL_RE.search(serialized):
            print("    WARN Mem0 MCP URL is unusual; expected https://mcp.mem0.ai/mcp")
        if "MEM0_API_KEY" not in serialized and "@mem0/opencode-plugin" not in serialized:
            print("    WARN no MEM0_API_KEY reference found; verify auth is configured elsewhere")
        if SECRET_RE.search(serialized):
            print("    WARN literal secret-looking token found; prefer environment variable interpolation")
            issues = max(issues, 1)
    return issues


def parse_toml_sections(text: str) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    current = ""
    sections[current] = {}
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
            sections.setdefault(current, {})
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            sections.setdefault(current, {})[key.strip()] = value.strip().strip('"')
    return sections


def check_toml(path: Path) -> int:
    try:
        text = path.read_text()
    except OSError as exc:
        print(f"{path}: ERROR cannot read: {exc}")
        return 1

    sections = parse_toml_sections(text)
    mem0_sections = {name: values for name, values in sections.items() if name.endswith(".mem0") or "mcp.mem0.ai/mcp" in str(values)}
    print(f"{path}: TOML-like parsed")
    if not mem0_sections:
        print("  WARN no [mcp_servers.mem0] section found")
    else:
        for name, values in mem0_sections.items():
            print(f"  - [{name}]: {json.dumps(redact(values), sort_keys=True)}")
            url = values.get("url", "")
            if url and not MEM0_URL_RE.search(url):
                print("    WARN Mem0 MCP URL is unusual; expected https://mcp.mem0.ai/mcp")
            if values.get("bearer_token_env_var") != "MEM0_API_KEY" and "MEM0_API_KEY" not in str(values):
                print("    WARN Codex direct MCP normally uses bearer_token_env_var = \"MEM0_API_KEY\"")

    features = sections.get("features", {})
    if "codex" in path.as_posix() or "config.toml" in path.name:
        if features.get("codex_hooks") != "true":
            print("  INFO Codex lifecycle hooks require [features] codex_hooks = true when hooks are installed")
    if SECRET_RE.search(text):
        print("  WARN literal secret-looking token found; prefer environment variable interpolation")
        return 1
    return 0


def infer_kind(path: Path, explicit: str) -> str:
    if explicit != "auto":
        return explicit
    suffix = path.suffix.lower()
    if suffix == ".json" or path.name in {"opencode.json", "mcp.json", "hooks.json"}:
        return "json"
    if suffix == ".toml" or path.name == "config.toml":
        return "toml"
    return "text"


def check_text(path: Path) -> int:
    try:
        text = path.read_text()
    except OSError as exc:
        print(f"{path}: ERROR cannot read: {exc}")
        return 1
    print(f"{path}: text scanned")
    if "mcp.mem0.ai/mcp" not in text and "MEM0_API_KEY" not in text and "@mem0" not in text:
        print("  WARN no Mem0-looking strings found")
    if text.count("mcp.mem0.ai/mcp") > 1:
        print("  WARN multiple Mem0 MCP URL occurrences; check for duplicates")
    if SECRET_RE.search(text):
        print("  WARN literal secret-looking token found; prefer environment variable interpolation")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Mem0 MCP/plugin config validator.")
    parser.add_argument("paths", nargs="*", help="Config files to inspect. Missing files are reported and skipped.")
    parser.add_argument("--kind", choices=["auto", "json", "toml", "text"], default="auto", help="Parser to use for all paths.")
    args = parser.parse_args()

    if not args.paths:
        parser.print_help()
        return 0

    exit_code = 0
    for raw_path in args.paths:
        path = Path(raw_path).expanduser()
        if not path.exists():
            print(f"{path}: WARN file does not exist")
            continue
        kind = infer_kind(path, args.kind)
        if kind == "json":
            exit_code = max(exit_code, check_json(path))
        elif kind == "toml":
            exit_code = max(exit_code, check_toml(path))
        else:
            exit_code = max(exit_code, check_text(path))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
