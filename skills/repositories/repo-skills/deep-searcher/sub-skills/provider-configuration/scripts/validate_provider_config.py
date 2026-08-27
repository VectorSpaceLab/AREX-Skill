#!/usr/bin/env python3
"""Validate DeepSearcher provider configuration without calling provider APIs.

This helper checks provider names, feature keys, and config shapes. When
--check-imports is enabled it imports the configured provider modules/classes to
surface missing optional SDKs, but it still does not instantiate providers,
contact networks, or open vector databases.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover - depends on caller environment
    yaml = None

FEATURES = ("llm", "embedding", "file_loader", "web_crawler", "vector_db")

DEFAULT_CONFIG = {
    "provide_settings": {
        "llm": {"provider": "OpenAI", "config": {"model": "o1-mini"}},
        "embedding": {"provider": "OpenAIEmbedding", "config": {"model": "text-embedding-ada-002"}},
        "file_loader": {"provider": "PDFLoader", "config": {}},
        "web_crawler": {"provider": "FireCrawlCrawler", "config": {}},
        "vector_db": {
            "provider": "Milvus",
            "config": {"default_collection": "deepsearcher", "uri": "./milvus.db", "token": "root:Milvus", "db": "default"},
        },
    },
    "query_settings": {"max_iter": 3},
    "load_settings": {"chunk_size": 1500, "chunk_overlap": 100},
}

EXAMPLES: dict[str, dict[str, Any]] = {
    "openai-default": DEFAULT_CONFIG,
    "ollama-fastembed-milvus": {
        "provide_settings": {
            "llm": {"provider": "Ollama", "config": {"model": "qwq"}},
            "embedding": {"provider": "FastEmbedEmbedding", "config": {"model": "BAAI/bge-small-en-v1.5"}},
            "file_loader": {"provider": "PDFLoader", "config": {}},
            "web_crawler": {"provider": "FireCrawlCrawler", "config": {}},
            "vector_db": {"provider": "Milvus", "config": {"uri": "./milvus.db", "token": ""}},
        },
        "query_settings": {"max_iter": 3},
        "load_settings": {"chunk_size": 1500, "chunk_overlap": 100},
    },
    "docling-local": {
        "provide_settings": {
            "llm": {"provider": "OpenAI", "config": {"model": "o1-mini"}},
            "embedding": {"provider": "OpenAIEmbedding", "config": {"model": "text-embedding-ada-002"}},
            "file_loader": {"provider": "DoclingLoader", "config": {}},
            "web_crawler": {"provider": "DoclingCrawler", "config": {}},
            "vector_db": {"provider": "Milvus", "config": {"uri": "./milvus.db", "token": ""}},
        },
        "query_settings": {"max_iter": 3},
        "load_settings": {"chunk_size": 1500, "chunk_overlap": 100},
    },
    "unstructured-local": {
        "provide_settings": {
            "llm": {"provider": "OpenAI", "config": {"model": "o1-mini"}},
            "embedding": {"provider": "OpenAIEmbedding", "config": {"model": "text-embedding-ada-002"}},
            "file_loader": {"provider": "UnstructuredLoader", "config": {}},
            "web_crawler": {"provider": "FireCrawlCrawler", "config": {}},
            "vector_db": {"provider": "Milvus", "config": {"uri": "./milvus.db", "token": ""}},
        },
        "query_settings": {"max_iter": 3},
        "load_settings": {"chunk_size": 1500, "chunk_overlap": 100},
    },
}

REGISTRY = {
    "llm": {
        "OpenAI": ("deepsearcher.llm", "OpenAI"),
        "DeepSeek": ("deepsearcher.llm", "DeepSeek"),
        "AzureOpenAI": ("deepsearcher.llm", "AzureOpenAI"),
        "Anthropic": ("deepsearcher.llm", "Anthropic"),
        "Ollama": ("deepsearcher.llm", "Ollama"),
        "WatsonX": ("deepsearcher.llm", "WatsonX"),
        "Bedrock": ("deepsearcher.llm", "Bedrock"),
        "TogetherAI": ("deepsearcher.llm", "TogetherAI"),
        "XAI": ("deepsearcher.llm", "XAI"),
        "Gemini": ("deepsearcher.llm", "Gemini"),
        "GLM": ("deepsearcher.llm", "GLM"),
        "Volcengine": ("deepsearcher.llm", "Volcengine"),
        "JiekouAI": ("deepsearcher.llm", "JiekouAI"),
        "Aliyun": ("deepsearcher.llm", "Aliyun"),
        "PPIO": ("deepsearcher.llm", "PPIO"),
        "SiliconFlow": ("deepsearcher.llm", "SiliconFlow"),
        "Novita": ("deepsearcher.llm", "Novita"),
    },
    "embedding": {
        "OpenAIEmbedding": ("deepsearcher.embedding", "OpenAIEmbedding"),
        "MilvusEmbedding": ("deepsearcher.embedding", "MilvusEmbedding"),
        "FastEmbedEmbedding": ("deepsearcher.embedding", "FastEmbedEmbedding"),
        "SentenceTransformerEmbedding": ("deepsearcher.embedding", "SentenceTransformerEmbedding"),
        "WatsonXEmbedding": ("deepsearcher.embedding", "WatsonXEmbedding"),
        "VoyageEmbedding": ("deepsearcher.embedding", "VoyageEmbedding"),
        "OllamaEmbedding": ("deepsearcher.embedding", "OllamaEmbedding"),
        "GeminiEmbedding": ("deepsearcher.embedding", "GeminiEmbedding"),
        "GLMEmbedding": ("deepsearcher.embedding", "GLMEmbedding"),
        "VolcengineEmbedding": ("deepsearcher.embedding", "VolcengineEmbedding"),
        "JiekouAIEmbedding": ("deepsearcher.embedding", "JiekouAIEmbedding"),
        "NovitaEmbedding": ("deepsearcher.embedding", "NovitaEmbedding"),
        "PPIOEmbedding": ("deepsearcher.embedding", "PPIOEmbedding"),
        "SiliconflowEmbedding": ("deepsearcher.embedding", "SiliconflowEmbedding"),
        "BedrockEmbedding": ("deepsearcher.embedding", "BedrockEmbedding"),
    },
    "file_loader": {
        "PDFLoader": ("deepsearcher.loader.file_loader", "PDFLoader"),
        "TextLoader": ("deepsearcher.loader.file_loader", "TextLoader"),
        "JsonFileLoader": ("deepsearcher.loader.file_loader", "JsonFileLoader"),
        "UnstructuredLoader": ("deepsearcher.loader.file_loader", "UnstructuredLoader"),
        "DoclingLoader": ("deepsearcher.loader.file_loader", "DoclingLoader"),
    },
    "web_crawler": {
        "FireCrawlCrawler": ("deepsearcher.loader.web_crawler", "FireCrawlCrawler"),
        "Crawl4AICrawler": ("deepsearcher.loader.web_crawler", "Crawl4AICrawler"),
        "JinaCrawler": ("deepsearcher.loader.web_crawler", "JinaCrawler"),
        "DoclingCrawler": ("deepsearcher.loader.web_crawler", "DoclingCrawler"),
    },
    "vector_db": {
        "Milvus": ("deepsearcher.vector_db", "Milvus"),
        "Qdrant": ("deepsearcher.vector_db", "Qdrant"),
        "OracleDB": ("deepsearcher.vector_db", "OracleDB"),
        "AzureSearch": ("deepsearcher.vector_db", "AzureSearch"),
    },
}


@dataclass
class Issue:
    severity: str
    feature: str
    provider: str
    message: str


@dataclass
class ImportCheck:
    feature: str
    provider: str
    module: str
    class_name: str
    ok: bool
    message: str = ""


class ConfigError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate DeepSearcher provider configurations safely.")
    parser.add_argument("--config", type=Path, help="Path to a YAML or JSON config file.")
    parser.add_argument("--list-providers", action="store_true", help="List known providers by feature and exit.")
    parser.add_argument(
        "--print-example",
        choices=sorted(EXAMPLES),
        help="Print one built-in config example as JSON and exit.",
    )
    parser.add_argument("--check-imports", action="store_true", help="Import provider modules/classes without instantiating them.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable output.")
    return parser.parse_args()


def load_config(path: Path | None) -> dict[str, Any]:
    if path is None:
        return DEFAULT_CONFIG
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(raw)
    if yaml is None:
        raise ConfigError("PyYAML is required to parse YAML configs in this environment.")
    return yaml.safe_load(raw)


def iter_feature_providers(config: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    provide_settings = config.get("provide_settings")
    if not isinstance(provide_settings, dict):
        raise ConfigError("Config must contain a top-level provide_settings mapping.")
    rows: list[tuple[str, str, dict[str, Any]]] = []
    for feature in FEATURES:
        section = provide_settings.get(feature)
        if not isinstance(section, dict):
            raise ConfigError(f"provide_settings.{feature} must be a mapping.")
        provider = section.get("provider")
        cfg = section.get("config") or {}
        if not isinstance(provider, str) or not provider:
            raise ConfigError(f"provide_settings.{feature}.provider must be a non-empty string.")
        if not isinstance(cfg, dict):
            raise ConfigError(f"provide_settings.{feature}.config must be a mapping.")
        rows.append((feature, provider, cfg))
    return rows


def validate_config(config: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    provide_settings = config.get("provide_settings")
    if not isinstance(provide_settings, dict):
        issues.append(Issue("error", "config", "<root>", "Missing top-level provide_settings mapping."))
        return issues

    for feature in FEATURES:
        section = provide_settings.get(feature)
        if not isinstance(section, dict):
            issues.append(Issue("error", feature, "<missing>", f"Missing provide_settings.{feature}."))
            continue
        provider = section.get("provider")
        if not isinstance(provider, str) or not provider:
            issues.append(Issue("error", feature, "<invalid>", "provider must be a non-empty string."))
            continue
        if provider not in REGISTRY[feature]:
            issues.append(
                Issue(
                    "error",
                    feature,
                    provider,
                    f"Unknown provider for {feature}. Use one of: {', '.join(sorted(REGISTRY[feature]))}.",
                )
            )
        cfg = section.get("config")
        if cfg is None:
            continue
        if not isinstance(cfg, dict):
            issues.append(Issue("error", feature, provider, "config must be a mapping or omitted."))

    for extra_section in ("query_settings", "load_settings"):
        if extra_section in config and not isinstance(config[extra_section], dict):
            issues.append(Issue("error", extra_section, "<root>", f"{extra_section} must be a mapping."))

    loader = provide_settings.get("file_loader")
    if isinstance(loader, dict) and loader.get("provider") == "JsonFileLoader":
        loader_cfg = loader.get("config") or {}
        if isinstance(loader_cfg, dict) and loader_cfg.get("text_key") not in {None, "text"}:
            issues.append(
                Issue(
                    "warning",
                    "file_loader",
                    "JsonFileLoader",
                    "The inspected corpus examples use text_key='text'; a different key may not work with the benchmark corpus.",
                )
            )

    return issues


def check_imports(config: dict[str, Any]) -> list[ImportCheck]:
    checks: list[ImportCheck] = []
    for feature, provider, _ in iter_feature_providers(config):
        module_name, class_name = REGISTRY[feature][provider]
        try:
            module = importlib.import_module(module_name)
            getattr(module, class_name)
        except Exception as exc:  # pragma: no cover - environment dependent
            checks.append(ImportCheck(feature, provider, module_name, class_name, False, f"{type(exc).__name__}: {exc}"))
        else:
            checks.append(ImportCheck(feature, provider, module_name, class_name, True))
    return checks


def print_provider_list() -> None:
    for feature in FEATURES:
        print(f"[{feature}]")
        for provider in sorted(REGISTRY[feature]):
            module, class_name = REGISTRY[feature][provider]
            print(f"  - {provider} -> {module}:{class_name}")


def print_example(name: str) -> None:
    print(json.dumps(EXAMPLES[name], indent=2, sort_keys=True))


def main() -> int:
    args = parse_args()

    if args.list_providers:
        print_provider_list()
        return 0
    if args.print_example:
        print_example(args.print_example)
        return 0

    try:
        config = load_config(args.config)
        issues = validate_config(config)
    except Exception as exc:
        if args.json:
            print(json.dumps({"ok": False, "errors": [f"{type(exc).__name__}: {exc}"], "imports": []}, indent=2, sort_keys=True))
        else:
            print(f"FAIL: {type(exc).__name__}: {exc}")
        return 2

    import_checks = check_imports(config) if args.check_imports else []
    ok = not any(issue.severity == "error" for issue in issues) and all(check.ok for check in import_checks)
    payload = {
        "ok": ok,
        "issues": [asdict(issue) for issue in issues],
        "imports": [asdict(check) for check in import_checks],
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        status = "PASS" if ok else "FAIL"
        print(f"{status}: provider configuration validation")
        for issue in issues:
            print(f"{issue.severity.upper()}: {issue.feature}/{issue.provider}: {issue.message}")
        for check in import_checks:
            if not check.ok:
                print(f"IMPORT FAIL: {check.feature}/{check.provider} -> {check.module}:{check.class_name}: {check.message}")
        if ok:
            print("No provider validation errors found.")

    return 0 if ok else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
