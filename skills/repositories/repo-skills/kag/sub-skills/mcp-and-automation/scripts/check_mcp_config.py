#!/usr/bin/env python3
"""Validate a KAG MCP launch or solver-side MCP config without starting a server.

Examples:
  python skills/disco/kag/sub-skills/mcp-and-automation/scripts/check_mcp_config.py
  python skills/disco/kag/sub-skills/mcp-and-automation/scripts/check_mcp_config.py ./kag_config.yaml --enabled-tools all --json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


SUPPORTED_TOOLS = ["qa-pipeline", "kb-retrieve"]


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


def load_config(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def normalize_tools(spec: str) -> List[str]:
    if spec == "all":
        return list(SUPPORTED_TOOLS)
    tools = [tool.strip() for tool in spec.split(",") if tool.strip()]
    return tools


def summarize(config: Dict[str, Any], transport: str, port: int, enabled_tools: str) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    requested = normalize_tools(enabled_tools)

    if importlib.util.find_spec("mcp") is None:
        errors.append("mcp package is not installed")

    unknown_tools = [tool for tool in requested if tool not in SUPPORTED_TOOLS]
    if unknown_tools:
        errors.append("unknown tool(s): " + ", ".join(unknown_tools))

    solver_pipeline = config.get("kag_solver_pipeline") if isinstance(config.get("kag_solver_pipeline"), dict) else config.get("solver_pipeline") if isinstance(config.get("solver_pipeline"), dict) else {}
    hybrid_executor = config.get("kag_hybrid_executor") if isinstance(config.get("kag_hybrid_executor"), dict) else {}
    vectorizer = config.get("vectorize_model") if isinstance(config.get("vectorize_model"), dict) else config.get("vectorizer") if isinstance(config.get("vectorizer"), dict) else {}
    llm_sections = [name for name in ("llm", "chat_llm", "openie_llm", "ner_llm") if isinstance(config.get(name), dict)]
    llm_available = bool(llm_sections)
    kb = config.get("kb") if isinstance(config.get("kb"), list) else []

    kb_server_names: List[str] = []
    if isinstance(kb, list):
        for item in kb:
            if isinstance(item, dict):
                mcp_servers = item.get("mcp_servers")
                if isinstance(mcp_servers, dict):
                    kb_server_names.extend(sorted(mcp_servers.keys()))

    tool_checks: Dict[str, Dict[str, Any]] = {}
    for tool in requested:
        if tool == "qa-pipeline":
            ready = bool(solver_pipeline)
            if not ready:
                warnings.append("qa-pipeline needs kag_solver_pipeline or solver_pipeline")
            if not llm_available:
                warnings.append("qa-pipeline usually needs an llm section such as llm, chat_llm, or openie_llm")
            tool_checks[tool] = {
                "ready": ready and llm_available,
                "required_sections": ["kag_solver_pipeline", "llm/chat_llm/openie_llm"],
            }
        elif tool == "kb-retrieve":
            ready = bool(hybrid_executor)
            if not ready:
                warnings.append("kb-retrieve needs kag_hybrid_executor")
            if not llm_available:
                warnings.append("kb-retrieve usually needs an llm section such as llm, chat_llm, or openie_llm")
            if not vectorizer:
                warnings.append("kb-retrieve usually needs a vectorize_model or vectorizer section")
            tool_checks[tool] = {
                "ready": ready and bool(vectorizer),
                "required_sections": ["kag_hybrid_executor", "vectorize_model/vectorizer"],
            }

    if transport not in {"stdio", "sse"}:
        errors.append(f"unknown transport: {transport}")

    if port <= 0 or port > 65535:
        errors.append(f"invalid port: {port}")

    if requested and not tool_checks:
        warnings.append("no known tools were selected")

    server_ready = not errors and importlib.util.find_spec("mcp") is not None
    solver_ready = bool(solver_pipeline)
    hybrid_ready = bool(hybrid_executor)

    return {
        "transport": transport,
        "port": port,
        "enabled_tools": requested,
        "server": {
            "mcp_package": importlib.util.find_spec("mcp") is not None,
            "server_ready": server_ready,
            "supported_tools": SUPPORTED_TOOLS,
        },
        "tool_checks": tool_checks,
        "solver_sections": {
            "kag_solver_pipeline": solver_ready,
            "kag_hybrid_executor": hybrid_ready,
            "llm_sections": llm_sections,
            "vectorize_model": bool(vectorizer),
            "kb_server_names": kb_server_names,
        },
        "warnings": warnings,
        "errors": errors,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a KAG MCP launch plan.")
    parser.add_argument("config", nargs="?", help="Config path. Defaults to the nearest kag_config.yaml from the current directory.")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio", help="Requested MCP transport to validate.")
    parser.add_argument("--port", type=int, default=3000, help="Requested SSE port to validate.")
    parser.add_argument("--enabled-tools", default="qa-pipeline", help="Comma-separated tool list, or 'all'.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable output.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cfg_path = Path(args.config).expanduser() if args.config else find_nearest_config(Path.cwd())
    if cfg_path is None:
        print("No kag_config.yaml found. Pass a config path explicitly.")
        return 1

    try:
        config = load_config(cfg_path)
    except Exception as exc:
        print(f"Failed to read {cfg_path}: {exc}")
        return 1

    result = summarize(config, args.transport, args.port, args.enabled_tools)
    result["config_file"] = str(cfg_path)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"config: {cfg_path}")
        print(f"transport: {result['transport']}")
        print(f"port: {result['port']}")
        print("enabled tools: " + ", ".join(result["enabled_tools"]))
        print("server ready: " + ("yes" if result["server"]["server_ready"] else "no"))
        if result["solver_sections"]["kb_server_names"]:
            print("kb mcp servers: " + ", ".join(result["solver_sections"]["kb_server_names"]))
        for tool, info in result["tool_checks"].items():
            print(f"{tool}: {'ready' if info['ready'] else 'not ready'}")
        if result["warnings"]:
            print("warnings:")
            for warning in result["warnings"]:
                print(f"- {warning}")
        if result["errors"]:
            print("errors:")
            for error in result["errors"]:
                print(f"- {error}")

    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
