#!/usr/bin/env python3
"""Check importability of Superduper first-party plugins.

The checker is deterministic and network-free: it imports only the requested
modules and prints package install hints for missing plugins. It never installs
packages, reads credentials, opens sockets, downloads models, or calls APIs.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class PluginInfo:
    key: str
    package: str
    module: str
    purpose: str
    aliases: tuple[str, ...] = ()


KNOWN_PLUGINS: dict[str, PluginInfo] = {
    "mongodb": PluginInfo(
        key="mongodb",
        package="superduper_mongodb",
        module="superduper_mongodb",
        purpose="MongoDB, Atlas, and mongomock data backend; Atlas vector search export",
        aliases=("mongo", "mongomock", "atlas"),
    ),
    "sql": PluginInfo(
        key="sql",
        package="superduper_sql",
        module="superduper_sql",
        purpose="SQL data backends including sqlite, duckdb, postgresql, mssql, and mysql schemes",
        aliases=("sqlite", "duckdb", "postgres", "postgresql", "mssql", "mysql", "ibis"),
    ),
    "snowflake": PluginInfo(
        key="snowflake",
        package="superduper_snowflake",
        module="superduper_snowflake",
        purpose="Snowflake data backend, database listener, secret helpers, and vector search export",
    ),
    "redis": PluginInfo(
        key="redis",
        package="superduper_redis",
        module="superduper_redis",
        purpose="Redis data backend",
    ),
    "chromadb": PluginInfo(
        key="chromadb",
        package="superduper-chromadb",
        module="superduper_chromadb",
        purpose="Chroma vector search export",
        aliases=("chroma",),
    ),
    "lance": PluginInfo(
        key="lance",
        package="superduper_lance",
        module="superduper_lance",
        purpose="Lance vector search export",
    ),
    "qdrant": PluginInfo(
        key="qdrant",
        package="superduper_qdrant",
        module="superduper_qdrant",
        purpose="Qdrant vector search export",
    ),
    "openai": PluginInfo(
        key="openai",
        package="superduper_openai",
        module="superduper_openai",
        purpose="OpenAI embedding and chat completion components",
    ),
    "anthropic": PluginInfo(
        key="anthropic",
        package="superduper_anthropic",
        module="superduper_anthropic",
        purpose="Anthropic completions component",
    ),
    "cohere": PluginInfo(
        key="cohere",
        package="superduper_cohere",
        module="superduper_cohere",
        purpose="Cohere embedding and generation components",
    ),
    "jina": PluginInfo(
        key="jina",
        package="superduper_jina",
        module="superduper_jina",
        purpose="Jina embedding component",
    ),
    "llamacpp": PluginInfo(
        key="llamacpp",
        package="superduper_llamacpp",
        module="superduper_llamacpp",
        purpose="Llama.cpp local LLM and embedding components",
        aliases=("llama_cpp", "llama-cpp", "llama", "llamacpp"),
    ),
    "vllm": PluginInfo(
        key="vllm",
        package="superduper_vllm",
        module="superduper_vllm",
        purpose="vLLM chat and completion components",
    ),
    "sentence_transformers": PluginInfo(
        key="sentence_transformers",
        package="superduper_sentence_transformers",
        module="superduper_sentence_transformers",
        purpose="Sentence Transformers embedding component",
        aliases=("sentence-transformers", "sbert"),
    ),
    "transformers": PluginInfo(
        key="transformers",
        package="superduper_transformers",
        module="superduper_transformers",
        purpose="Hugging Face Transformers pipeline, LLM, and trainer components",
        aliases=("hf", "huggingface", "hugging-face"),
    ),
    "torch": PluginInfo(
        key="torch",
        package="superduper_torch",
        module="superduper_torch",
        purpose="PyTorch model, trainer, tensor encoder, and decorator helpers",
        aliases=("pytorch",),
    ),
    "sklearn": PluginInfo(
        key="sklearn",
        package="superduper_sklearn",
        module="superduper_sklearn",
        purpose="scikit-learn estimator and trainer components",
        aliases=("scikit-learn", "scikit_learn"),
    ),
    "pillow": PluginInfo(
        key="pillow",
        package="superduper_pillow",
        module="superduper_pillow",
        purpose="Pillow image encoder helper",
        aliases=("image", "pil"),
    ),
    "template": PluginInfo(
        key="template",
        package="superduper_template",
        module="superduper_template",
        purpose="Plugin template package; not usually a runtime integration",
    ),
}


def normalize_name(name: str) -> str:
    normalized = name.strip().lower().replace("-", "_")
    if normalized.startswith("superduper_"):
        normalized = normalized[len("superduper_") :]
    return normalized


def build_alias_map() -> dict[str, str]:
    aliases: dict[str, str] = {}
    for key, info in KNOWN_PLUGINS.items():
        candidates = {
            key,
            info.package,
            info.module,
            info.package.replace("-", "_"),
            info.package.replace("_", "-"),
            *info.aliases,
        }
        for candidate in candidates:
            aliases[normalize_name(candidate)] = key
    return aliases


ALIASES = build_alias_map()


def resolve_plugin(name: str) -> PluginInfo:
    normalized = normalize_name(name)
    key = ALIASES.get(normalized)
    if key is not None:
        return KNOWN_PLUGINS[key]
    guessed = normalized.replace("-", "_")
    return PluginInfo(
        key=guessed,
        package=f"superduper_{guessed}",
        module=f"superduper_{guessed}",
        purpose="User-supplied Superduper plugin name; guessed from superduper_<name> convention",
    )


def unique_plugins(infos: Iterable[PluginInfo]) -> list[PluginInfo]:
    seen: set[str] = set()
    unique: list[PluginInfo] = []
    for info in infos:
        marker = info.module
        if marker in seen:
            continue
        seen.add(marker)
        unique.append(info)
    return unique


def check_import(info: PluginInfo) -> dict[str, object]:
    result: dict[str, object] = {
        "key": info.key,
        "package": info.package,
        "module": info.module,
        "purpose": info.purpose,
        "ok": False,
        "version": None,
        "error_type": None,
        "error": None,
        "missing_name": None,
        "install_hint": f"python -m pip install {info.package}",
    }
    try:
        module = importlib.import_module(info.module)
    except ModuleNotFoundError as exc:
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
        result["missing_name"] = exc.name
        return result
    except Exception as exc:  # noqa: BLE001 - report import-time failures without hiding them.
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
        return result

    result["ok"] = True
    result["version"] = getattr(module, "__version__", None)
    return result


def print_known() -> None:
    print("Known first-party Superduper plugins:")
    for key in sorted(KNOWN_PLUGINS):
        info = KNOWN_PLUGINS[key]
        alias_text = f" aliases={', '.join(info.aliases)}" if info.aliases else ""
        print(f"- {key}: package={info.package} module={info.module}{alias_text}")


def print_text_results(results: list[dict[str, object]]) -> None:
    for result in results:
        key = result["key"]
        module = result["module"]
        package = result["package"]
        if result["ok"]:
            version = result.get("version") or "unknown-version"
            print(f"OK {key}: imported {module} ({version})")
            continue

        print(f"MISSING {key}: could not import {module}")
        missing_name = result.get("missing_name")
        error = result.get("error")
        if missing_name and missing_name != module:
            print(f"  Missing dependency during plugin import: {missing_name}")
        if error:
            print(f"  Error: {error}")
        print(f"  Install hint: {result['install_hint']}")
        print(
            "  Boundary: import checks do not verify credentials, services, GPU runtime, "
            "model weights, or live API calls."
        )
        if package == "superduper-chromadb":
            print("  Note: Chroma package uses a hyphen; import module uses an underscore.")
        if key == "llamacpp":
            print("  Note: use module superduper_llamacpp, not superduper_llama_cpp.")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import-check selected Superduper first-party plugins without installing "
            "packages, reading credentials, opening network connections, or calling APIs."
        )
    )
    parser.add_argument(
        "plugins",
        nargs="*",
        help=(
            "Plugin names, package names, or import modules to check, e.g. "
            "mongodb sqlite openai superduper-chromadb. Unknown names are checked "
            "as superduper_<name>."
        ),
    )
    parser.add_argument(
        "--all-known",
        action="store_true",
        help="Check every known first-party plugin in the embedded catalog.",
    )
    parser.add_argument(
        "--list-known",
        action="store_true",
        help="List known plugin names, packages, modules, and aliases, then exit 0.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON results instead of text.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    if args.list_known:
        if args.json:
            print(json.dumps({k: asdict(v) for k, v in sorted(KNOWN_PLUGINS.items())}, indent=2))
        else:
            print_known()
        return 0

    requested: list[PluginInfo] = []
    if args.all_known:
        requested.extend(KNOWN_PLUGINS[key] for key in sorted(KNOWN_PLUGINS))
    requested.extend(resolve_plugin(name) for name in args.plugins)
    requested = unique_plugins(requested)

    if not requested:
        if args.json:
            print(json.dumps([], indent=2))
        else:
            print("No plugins requested. Use --list-known or pass plugin names such as mongodb sqlite openai.")
        return 0

    results = [check_import(info) for info in requested]
    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        print_text_results(results)

    return 1 if any(not result["ok"] for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
