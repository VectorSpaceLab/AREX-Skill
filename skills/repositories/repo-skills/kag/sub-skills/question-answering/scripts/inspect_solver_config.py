#!/usr/bin/env python3
"""Inspect a KAG solver config and print a redacted summary.

Examples:
  python skills/disco/kag/sub-skills/question-answering/scripts/inspect_solver_config.py
  python skills/disco/kag/sub-skills/question-answering/scripts/inspect_solver_config.py ./kag_config.yaml --json
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


SENSITIVE_KEYS = {"api_key", "key", "token", "secret", "password", "passwd"}


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


def redacted_value(key: str, value: Any) -> Any:
    if isinstance(value, dict):
        return {k: redacted_value(k, v) for k, v in value.items() if not k.startswith("_")}
    if isinstance(value, list):
        return [redacted_value(key, item) for item in value]
    if isinstance(value, str):
        lower = key.lower()
        if lower in SENSITIVE_KEYS or any(token in lower for token in ("secret", "token", "password")):
            return "<redacted>"
        pathish_key = any(token in lower for token in ("path", "file", "dir", "cwd", "schema"))
        if pathish_key and "://" not in value:
            stripped = value.strip()
            if stripped.startswith(("/", "~", "./", "../")) or "\\" in stripped or os.sep in stripped:
                return "<path>"
    return value


def summarize_mapping(mapping: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key in keys:
        if key in mapping:
            result[key] = redacted_value(key, mapping[key])
    return result


def pipeline_summary(config: Dict[str, Any]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {}
    for key in ("kag_solver_pipeline", "solver_pipeline", "index_pipeline", "static_solver_pipeline", "iterative_solver_pipeline", "self_cognition_pipeline", "mcp_pipeline"):
        if key in config:
            block = config[key]
            if isinstance(block, dict):
                block_summary = {
                    "type": block.get("type"),
                    "planner_type": (block.get("planner") or {}).get("type") if isinstance(block.get("planner"), dict) else None,
                    "generator_type": (block.get("generator") or {}).get("type") if isinstance(block.get("generator"), dict) else None,
                    "executor_types": [item.get("type") for item in block.get("executors", []) if isinstance(item, dict)] if isinstance(block.get("executors"), list) else None,
                    "max_iterations": block.get("max_iterations", block.get("max_iteration")),
                }
                summary[key] = {k: v for k, v in block_summary.items() if v not in (None, [], {})}
    return summary


def kb_summary(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    kbs = config.get("kb", [])
    if not isinstance(kbs, list):
        return []
    out: List[Dict[str, Any]] = []
    for kb in kbs:
        if not isinstance(kb, dict):
            continue
        project = kb.get("project", {}) if isinstance(kb.get("project"), dict) else {}
        mcp_servers = kb.get("mcp_servers", {}) if isinstance(kb.get("mcp_servers"), dict) else {}
        out.append(
            {
                "id": kb.get("id") or project.get("id"),
                "project_id": project.get("id"),
                "namespace": project.get("namespace"),
                "index_list": kb.get("index_list", []),
                "vectorizer_type": (kb.get("vectorizer") or {}).get("type") if isinstance(kb.get("vectorizer"), dict) else None,
                "mcp_servers": sorted(mcp_servers.keys()),
            }
        )
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect a KAG solver config.")
    parser.add_argument("config", nargs="?", help="Config path. Defaults to the nearest kag_config.yaml from the current directory.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable output.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cfg_path = Path(args.config).expanduser() if args.config else find_nearest_config(Path.cwd())
    if cfg_path is None:
        print("No kag_config.yaml found. Pass a config path explicitly.")
        return 1

    try:
        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        print(f"Failed to read {cfg_path}: {exc}")
        return 1

    result = {
        "config_file": str(cfg_path),
        "top_level_keys": sorted(data.keys()),
        "project": summarize_mapping(data.get("project", {}) if isinstance(data.get("project"), dict) else {}, ["id", "namespace", "host_addr", "language", "biz_scene"]),
        "chat": summarize_mapping(data.get("chat", {}) if isinstance(data.get("chat"), dict) else {}, ["ename", "index_list"]),
        "kb": kb_summary(data),
        "pipelines": pipeline_summary(data),
        "llm": summarize_mapping(data.get("llm", {}) if isinstance(data.get("llm"), dict) else {}, ["type", "model", "base_url"]),
        "vectorize_model": summarize_mapping(data.get("vectorize_model", {}) if isinstance(data.get("vectorize_model"), dict) else {}, ["type", "model", "base_url", "vector_dimensions"]),
    }

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"config: {result['config_file']}")
        print("top-level keys: " + ", ".join(result["top_level_keys"]))
        if result["project"]:
            print("project:")
            for key, value in result["project"].items():
                print(f"  {key}: {value}")
        if result["chat"]:
            print("chat:")
            for key, value in result["chat"].items():
                print(f"  {key}: {value}")
        if result["kb"]:
            print("kb:")
            for kb in result["kb"]:
                print(json.dumps(kb, indent=2, ensure_ascii=False))
        if result["pipelines"]:
            print("pipelines:")
            print(json.dumps(result["pipelines"], indent=2, ensure_ascii=False))
        if result["llm"]:
            print("llm:")
            print(json.dumps(result["llm"], indent=2, ensure_ascii=False))
        if result["vectorize_model"]:
            print("vectorize_model:")
            print(json.dumps(result["vectorize_model"], indent=2, ensure_ascii=False))
        print("Use --json for machine-readable output.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
