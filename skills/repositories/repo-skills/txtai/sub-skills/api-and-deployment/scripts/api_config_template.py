#!/usr/bin/env python3
"""
Generate and validate minimal txtai API YAML configs without starting a server.

This helper intentionally avoids importing txtai.api or uvicorn. It is safe for
configuration planning, CI checks, and deployment handoffs where the service
should not be launched.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only in minimal environments
    yaml = None


TEMPLATES = {
    "secure-readonly": """# Read-only txtai API service template\n# Build or copy an index to this path before serving.\npath: ./index\nwritable: false\nreindex: false\n\nembeddings:\n  path: sentence-transformers/all-MiniLM-L6-v2\n  content: true\n\n# Optional compatibility surfaces. Remove what clients do not need.\nopenai: true\nmcp: true\n""",
    "writable-admin": """# Private/admin txtai API service template\n# Keep this service off public networks.\npath: ./index\nwritable: true\nreindex: false\n\nembeddings:\n  path: sentence-transformers/all-MiniLM-L6-v2\n  content: true\n""",
    "workflow-service": """# txtai API service exposing a named workflow\nworkflow:\n  echo:\n    tasks:\n      - task: console\n""",
    "openai-llm": """# OpenAI-compatible txtai API template backed by an LLM pipeline\nopenai: true\n\nllm:\n  path: hf-internal-testing/tiny-random-gpt2\n  task: language-generation\n""",
    "cluster-aggregator": """# txtai distributed embeddings cluster aggregator\n# Shards must be stable txtai API services with compatible indexes.\ncluster:\n  shards:\n    - http://txtai-shard-0:8000\n    - http://txtai-shard-1:8000\n""",
}

ROUTE_KEYS = {
    "agent",
    "caption",
    "cluster",
    "embeddings",
    "entity",
    "extractor",
    "labels",
    "llm",
    "mcp",
    "objects",
    "openai",
    "rag",
    "reranker",
    "segmentation",
    "similarity",
    "summary",
    "tabular",
    "textractor",
    "texttospeech",
    "transcription",
    "translation",
    "upload",
    "workflow",
}

MUTATION_KEYS = {"writable", "reindex"}


class ConfigError(ValueError):
    """Raised when a config fails validation."""


def parse_scalar(value: str):
    value = value.strip()
    lowered = value.lower()
    if lowered in {"true", "yes", "on"}:
        return True
    if lowered in {"false", "no", "off"}:
        return False
    if lowered in {"null", "none", "~"}:
        return None
    return value.strip("'\"")


def load_yaml_fallback(text: str) -> dict:
    """Parse enough YAML to validate top-level txtai API sections without PyYAML."""

    config = {}
    current = None
    nested = None

    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()

        if indent == 0 and ":" in stripped:
            key, value = stripped.split(":", 1)
            current, nested = key.strip(), None
            config[current] = parse_scalar(value) if value.strip() else {}
        elif indent > 0 and current and isinstance(config.get(current), dict):
            parent = config[current]
            if stripped.startswith("- ") and nested:
                parent.setdefault(nested, []).append(parse_scalar(stripped[2:]))
            elif ":" in stripped:
                key, value = stripped.split(":", 1)
                key, value = key.strip(), value.strip()
                parent[key] = parse_scalar(value) if value else []
                nested = key if not value else None

    return config


def load_yaml(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ConfigError(f"Config file not found: {path}") from exc

    if yaml is None:
        return load_yaml_fallback(text)

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML parse error in {path}: {exc}") from exc

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError("Top-level YAML value must be a mapping/dictionary.")

    return data


def validate_config(config: dict) -> list[str]:
    messages = []
    if yaml is None:
        messages.append("warning: PyYAML not available; used built-in top-level parser")

    enabled = sorted(key for key in config if key in ROUTE_KEYS)
    if enabled:
        messages.append("enabled route/config keys: " + ", ".join(enabled))
    else:
        messages.append("warning: no known API route keys found; /docs may contain only FastAPI defaults")

    if config.get("writable") is True:
        messages.append("warning: writable=true enables add/index/upsert/delete mutation routes")
    elif "embeddings" in config or "cluster" in config:
        messages.append("read-only posture: mutation routes should return 403 unless writable=true")

    if config.get("reindex") is True:
        if config.get("writable") is not True:
            messages.append("warning: reindex=true is ineffective unless writable=true")
        messages.append("warning: reindex=true should be exposed only to trusted admin callers")

    if config.get("openai") and not any(key in config for key in ("agent", "embeddings", "llm", "rag", "workflow")):
        messages.append("warning: openai=true needs a backing agent, embeddings, llm/rag pipeline, or workflow")

    if config.get("mcp") and not enabled:
        messages.append("warning: mcp is set but no other route keys are enabled")

    if "cluster" in config:
        shards = config.get("cluster", {}).get("shards") if isinstance(config.get("cluster"), dict) else None
        if not shards or not isinstance(shards, list):
            raise ConfigError("cluster.shards must be a non-empty list of shard API URLs.")
        messages.append(f"cluster shards: {len(shards)}")

    if "workflow" in config and not isinstance(config["workflow"], dict):
        raise ConfigError("workflow must be a mapping of workflow names to definitions.")

    if "agent" in config and not isinstance(config["agent"], dict):
        raise ConfigError("agent must be a mapping of agent names to definitions.")

    for key in MUTATION_KEYS:
        if key in config and not isinstance(config[key], bool):
            raise ConfigError(f"{key} must be a boolean when set.")

    return messages


def write_template(name: str, output: Path, force: bool) -> None:
    if output.exists() and not force:
        raise ConfigError(f"Refusing to overwrite existing file: {output}. Use --force to replace it.")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(TEMPLATES[name], encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate or validate minimal txtai API YAML configs without launching a server.")
    parser.add_argument("--template", choices=sorted(TEMPLATES), help="Template name to write.")
    parser.add_argument("--output", type=Path, help="Output YAML path for --template.")
    parser.add_argument("--force", action="store_true", help="Overwrite --output when it already exists.")
    parser.add_argument("--validate", type=Path, help="Validate an existing YAML config and summarize enabled route keys.")
    parser.add_argument("--list", action="store_true", help="List available templates.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        if args.list:
            for name in sorted(TEMPLATES):
                print(name)

        if args.template:
            if not args.output:
                raise ConfigError("--output is required with --template.")
            write_template(args.template, args.output, args.force)
            print(f"wrote {args.template} template to {args.output}")

        if args.validate:
            config = load_yaml(args.validate)
            print(f"validated {args.validate}")
            for message in validate_config(config):
                print(f"- {message}")

        if not any((args.list, args.template, args.validate)):
            raise ConfigError("Choose --list, --template, or --validate. Use --help for examples.")

    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
