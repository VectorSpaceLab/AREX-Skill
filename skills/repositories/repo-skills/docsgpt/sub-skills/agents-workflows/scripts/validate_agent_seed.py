#!/usr/bin/env python3
"""Offline structural validator for DocsGPT premade-agent seed YAML."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    raise SystemExit("PyYAML is required: python -m pip install PyYAML")

AGENT_TYPES = {"classic", "react", "agentic", "research", "workflow"}
LOADERS = {"url", "sitemap", "crawler", "reddit", "github", "s3"}
PLACEHOLDER = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("seed", type=Path)
    parser.add_argument("--require-env", action="store_true", help="Fail instead of warn for unresolved ${NAME} placeholders")
    args = parser.parse_args()
    try:
        data = yaml.safe_load(args.seed.read_text(encoding="utf-8")) or {}
    except Exception as error:
        print(f"ERROR: invalid YAML: {error}", file=sys.stderr)
        return 2
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(data, dict) or not isinstance(data.get("agents"), list):
        print("ERROR: top-level agents must be a list", file=sys.stderr)
        return 1
    names: set[str] = set()
    for index, agent in enumerate(data["agents"]):
        where = f"agents[{index}]"
        if not isinstance(agent, dict):
            errors.append(f"{where} must be an object")
            continue
        name = agent.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{where}.name must be non-empty")
        elif name in names:
            errors.append(f"duplicate agent name {name!r}")
        else:
            names.add(name)
        agent_type = agent.get("agent_type", "classic")
        if agent_type not in AGENT_TYPES:
            errors.append(f"{where}.agent_type must be one of {sorted(AGENT_TYPES)}")
        prompt = agent.get("prompt")
        if prompt is not None and (not isinstance(prompt, dict) or not isinstance(prompt.get("content"), str)):
            errors.append(f"{where}.prompt must contain string content")
        source = agent.get("source")
        if source is not None:
            if not isinstance(source, dict):
                errors.append(f"{where}.source must be an object")
            elif source.get("loader") not in LOADERS:
                errors.append(f"{where}.source.loader must be one of {sorted(LOADERS)}")
        tools = agent.get("tools", [])
        if tools is not None and not isinstance(tools, list):
            errors.append(f"{where}.tools must be a list")
        elif isinstance(tools, list):
            for tool_index, tool in enumerate(tools):
                if not isinstance(tool, dict) or not isinstance(tool.get("name"), str):
                    errors.append(f"{where}.tools[{tool_index}] requires a string name")
        for text in strings(agent):
            for env_name in PLACEHOLDER.findall(text):
                if env_name not in os.environ:
                    message = f"{where}: unresolved environment placeholder {env_name}"
                    (errors if args.require_env else warnings).append(message)
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"Validated {len(data['agents'])} agent seed definition(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
