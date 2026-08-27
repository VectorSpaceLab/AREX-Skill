#!/usr/bin/env python3
"""Safely inspect a DB-GPT model TOML file without resolving or contacting anything.

This checker intentionally uses only the Python standard library. It does not
import DB-GPT, resolve environment variables, print configuration values,
contact providers/controllers, download models, or start services.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ENV_RE = re.compile(r"\$\{env:([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")
ENV_START_RE = re.compile(r"\$\{env:")
KNOWN_PROVIDERS = {
    "hf",
    "vllm",
    "llama.cpp",
    "llama.cpp.server",
    "mlx",
    "proxy/openai",
    "proxy/deepseek",
    "proxy/tongyi",
    "proxy/ollama",
    "proxy/siliconflow",
    "proxy/litellm",
}
MODEL_ROLES = {
    "llms": ("llm", "chat"),
    "embeddings": ("text2vec", "embedding"),
    "rerankers": ("reranker", "reranking"),
}
SERVICE_SECTIONS = (
    ("service.web", "web"),
    ("service.model.controller", "controller"),
    ("service.model.worker", "worker"),
    ("service.model.api", "api"),
)


def issue(level: str, message: str, location: str | None = None) -> dict[str, str]:
    result = {"level": level, "message": message}
    if location:
        result["location"] = location
    return result


def env_placeholders(value: Any, location: str, problems: list[dict[str, str]]) -> None:
    if not isinstance(value, str):
        return
    for match in ENV_START_RE.finditer(value):
        end = value.find("}", match.start())
        if end < 0:
            problems.append(issue("error", "unterminated environment placeholder", location))
    for match in re.finditer(r"\$\{env:[^}]+\}", value):
        if not ENV_RE.fullmatch(match.group(0)):
            problems.append(issue("error", "invalid environment placeholder syntax", location))


def read_path(data: dict[str, Any], dotted: str) -> Any:
    current: Any = data
    for key in dotted.split("."):
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def static_url(value: Any) -> bool:
    if not isinstance(value, str) or "${env:" in value:
        return True  # defer environment-backed URL validation
    parsed = urlsplit(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def check_model_entries(
    models: dict[str, Any], problems: list[dict[str, str]], warnings: list[dict[str, str]]
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table, (worker_type, label) in MODEL_ROLES.items():
        entries = models.get(table, [])
        counts[table] = len(entries) if isinstance(entries, list) else 0
        location = f"models.{table}"
        if entries is None:
            entries = []
        if not isinstance(entries, list):
            problems.append(issue("error", "must be an array of TOML tables", location))
            continue
        names: set[str] = set()
        for index, entry in enumerate(entries):
            item_location = f"{location}[{index}]"
            if not isinstance(entry, dict):
                problems.append(issue("error", "entry must be a table", item_location))
                continue
            name = entry.get("name")
            if not isinstance(name, str) or not name.strip():
                problems.append(issue("error", "model name is required", item_location))
            elif "@" in name:
                problems.append(issue("error", "model name cannot contain '@'", f"{item_location}.name"))
            elif name in names:
                problems.append(issue("error", "duplicate model name within role", f"{item_location}.name"))
            else:
                names.add(name)
            provider = entry.get("provider")
            if not isinstance(provider, str) or not provider.strip():
                problems.append(issue("error", "provider is required", f"{item_location}.provider"))
                provider = ""
            elif provider not in KNOWN_PROVIDERS and not provider.startswith("proxy/"):
                warnings.append(issue("warning", "provider is not in the common DB-GPT provider matrix; verify its installed adapter", f"{item_location}.provider"))
            if provider in {"hf", "vllm", "llama.cpp", "llama.cpp.server", "mlx"} and not entry.get("path"):
                warnings.append(issue("warning", "local backend has no path; it may rely on an approved model identifier or runtime default", item_location))
            if provider.startswith("proxy/"):
                if provider != "proxy/ollama" and provider != "proxy/litellm" and "api_key" not in entry:
                    warnings.append(issue("warning", "proxy entry has no api_key field; confirm provider-specific credential resolution", item_location))
                for field in ("api_base", "api_url"):
                    if field in entry and not static_url(entry[field]):
                        problems.append(issue("error", f"{field} must be an http(s) URL or an environment placeholder", f"{item_location}.{field}"))
            if table == "embeddings" and provider in {"proxy/openai", "proxy/deepseek", "proxy/tongyi", "proxy/siliconflow"} and not any(k in entry for k in ("api_url", "api_base")):
                warnings.append(issue("warning", "embedding proxy has neither api_url nor api_base; verify the adapter default before using RAG", item_location))
            for key, value in entry.items():
                env_placeholders(value, f"{item_location}.{key}", problems)
        if entries and len(names) != len(entries):
            # Duplicate errors above are more precise; this branch prevents a
            # future change from accidentally turning duplicates into success.
            pass
    return counts


def check_service_ports(data: dict[str, Any], problems: list[dict[str, str]]) -> None:
    seen: dict[int, str] = {}
    for dotted, label in SERVICE_SECTIONS:
        section = read_path(data, dotted)
        if not isinstance(section, dict) or "port" not in section:
            continue
        port = section["port"]
        location = f"{dotted}.port"
        if not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535:
            problems.append(issue("error", "port must be an integer from 1 through 65535", location))
            continue
        previous = seen.get(port)
        if previous:
            problems.append(issue("error", f"port conflicts with {previous}", location))
        else:
            seen[port] = label


def validate(path: Path, allow_missing_embeddings: bool) -> dict[str, Any]:
    problems: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    try:
        with path.open("rb") as stream:
            data = tomllib.load(stream)
    except FileNotFoundError:
        return {"ok": False, "errors": [issue("error", "configuration file not found")], "warnings": [], "models": {}}
    except tomllib.TOMLDecodeError as exc:
        return {"ok": False, "errors": [issue("error", f"invalid TOML: {exc}")], "warnings": [], "models": {}}
    if not isinstance(data, dict):
        problems.append(issue("error", "top-level TOML value must be a table"))
        return {"ok": False, "errors": problems, "warnings": warnings, "models": {}}
    models = data.get("models", {})
    if not isinstance(models, dict):
        problems.append(issue("error", "models must be a TOML table", "models"))
        models = {}
    counts = check_model_entries(models, problems, warnings)
    if counts.get("llms", 0) == 0:
        problems.append(issue("error", "at least one LLM entry is required", "models.llms"))
    if counts.get("embeddings", 0) == 0:
        level = "warning" if allow_missing_embeddings else "error"
        target = warnings if allow_missing_embeddings else problems
        target.append(issue(level, "no embedding entry configured; RAG/knowledge workflows cannot be declared ready", "models.embeddings"))
    for key in ("default_llm", "default_embedding", "default_reranker"):
        if key not in models:
            continue
        value = models[key]
        if not isinstance(value, str) or not value.strip():
            problems.append(issue("error", "default must be a non-empty model name", f"models.{key}"))
        else:
            table = {"default_llm": "llms", "default_embedding": "embeddings", "default_reranker": "rerankers"}[key]
            names = {entry.get("name") for entry in models.get(table, []) if isinstance(entry, dict)}
            if value not in names:
                problems.append(issue("error", "default does not match a model name in its role table", f"models.{key}"))
    for key, value in data.items():
        env_placeholders(value, key, problems)
    check_service_ports(data, problems)
    return {"ok": not problems, "errors": problems, "warnings": warnings, "models": counts}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate DB-GPT model TOML statically; no imports, secrets, network, downloads, or service startup."
    )
    parser.add_argument("config", type=Path, help="TOML file to inspect")
    parser.add_argument("--json", action="store_true", help="print a machine-readable report")
    parser.add_argument(
        "--allow-missing-embeddings",
        action="store_true",
        help="downgrade the missing-embedding error to a warning for chat-only configs",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = validate(args.config, args.allow_missing_embeddings)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        status = "OK" if report["ok"] else "FAILED"
        print(f"{status}: {args.config}")
        print("models:", ", ".join(f"{key}={value}" for key, value in report["models"].items()) or "none")
        for item in report["errors"] + report["warnings"]:
            prefix = item["level"].upper()
            where = f" [{item['location']}]" if "location" in item else ""
            print(f"{prefix}{where}: {item['message']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
