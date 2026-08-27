#!/usr/bin/env python3
"""Inspect a KAG config file and print a redacted summary.

The script accepts a config path or discovers the nearest `kag_config.yaml`
from the current working directory. It understands the package's `!ENV` YAML
constructor and redacts obvious secret fields.

Examples:
  python skills/disco/kag/scripts/inspect_kag_config.py
  python skills/disco/kag/scripts/inspect_kag_config.py --config ./kag_config.yaml
  python skills/disco/kag/scripts/inspect_kag_config.py --json
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import yaml


SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "key",
    "token",
    "secret",
    "password",
    "passwd",
    "access_key",
    "access_token",
}

SUMMARY_KEYS = {
    "project": ["id", "namespace", "host_addr", "language", "biz_scene"],
    "llm": ["type", "model", "base_url", "enable_check"],
    "openie_llm": ["type", "model", "base_url", "enable_check"],
    "chat_llm": ["type", "model", "base_url", "enable_check"],
    "vectorize_model": ["type", "model", "base_url", "vector_dimensions", "enable_check"],
    "vectorizer": ["type", "model", "base_url", "vector_dimensions", "enable_check"],
    "kag_builder_pipeline": ["chain", "scanner", "num_threads_per_chain", "num_chains"],
    "kag_solver_pipeline": ["type", "planner", "executors", "generator", "max_iterations", "memory", "reasoner"],
    "mcp_executor": ["type", "name", "description", "store_path", "env"],
}


def add_env_constructor() -> None:
    def _env(loader: yaml.SafeLoader, node: yaml.Node) -> Any:
        value = loader.construct_scalar(node)
        return os.getenv(value.strip())

    yaml.SafeLoader.add_constructor("!ENV", _env)


add_env_constructor()


def find_nearest_config(start: Path) -> Optional[Path]:
    current = start.resolve()
    while True:
        candidate = current / "kag_config.yaml"
        if candidate.exists():
            return candidate
        if current.parent == current:
            return None
        current = current.parent


def redact_string(key: str, value: str) -> str:
    lower = key.lower()
    if lower in SENSITIVE_KEYS or any(token in lower for token in ("secret", "token", "password")):
        return "<redacted>"
    pathish_key = any(token in lower for token in ("path", "file", "dir", "cwd", "schema"))
    if pathish_key and isinstance(value, str) and "://" not in value:
        stripped = value.strip()
        if stripped.startswith(("/", "~", "./", "../")) or "\\" in stripped or os.sep in stripped:
            return "<path>"
    return value


def summarize(value: Any, key: str = "") -> Any:
    if isinstance(value, dict):
        summary: Dict[str, Any] = {}
        if key in SUMMARY_KEYS:
            keys: Iterable[str] = SUMMARY_KEYS[key]
        else:
            keys = value.keys()
        for child_key in keys:
            if child_key in value:
                summary[child_key] = summarize(value[child_key], child_key)
        extras = sorted(k for k in value.keys() if k not in summary and not k.startswith("_") and k not in SENSITIVE_KEYS)
        if extras and key in SUMMARY_KEYS:
            summary["extra_keys"] = extras
        elif not key in SUMMARY_KEYS:
            for child_key in extras:
                summary[child_key] = summarize(value[child_key], child_key)
        return summary
    if isinstance(value, list):
        return [summarize(item, key) for item in value]
    if isinstance(value, str):
        return redact_string(key, value)
    return value


def collect_highlights(config: Dict[str, Any]) -> Dict[str, Any]:
    highlights: Dict[str, Any] = {}
    for section in ("project", "llm", "openie_llm", "chat_llm", "vectorize_model", "vectorizer", "kag_builder_pipeline", "kag_solver_pipeline", "mcp_executor", "chat", "kb", "log"):
        if section in config:
            highlights[section] = summarize(config[section], section)
    return highlights


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect a KAG config file.")
    parser.add_argument("--config", help="Path to kag_config.yaml. Defaults to the nearest one from the current directory.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable output.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cfg_path = Path(args.config).expanduser() if args.config else find_nearest_config(Path.cwd())
    if cfg_path is None:
        print("No kag_config.yaml found. Pass --config explicitly.")
        return 1

    try:
        raw = cfg_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw) or {}
    except Exception as exc:
        print(f"Failed to read {cfg_path}: {exc}")
        return 1

    result = {
        "config_file": str(cfg_path),
        "top_level_keys": sorted(data.keys()),
        "summary": collect_highlights(data),
    }

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"config: {cfg_path}")
        print("top-level keys: " + ", ".join(result["top_level_keys"]))
        summary = result["summary"]
        if "project" in summary:
            print("project:")
            for key, value in summary["project"].items():
                print(f"  {key}: {value}")
        for section in ("llm", "openie_llm", "chat_llm", "vectorize_model", "vectorizer", "kag_builder_pipeline", "kag_solver_pipeline", "mcp_executor", "chat", "kb", "log"):
            if section in summary:
                print(f"{section}:")
                print(json.dumps(summary[section], indent=2, ensure_ascii=False))
        print("Use --json for machine-readable output.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
