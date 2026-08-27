#!/usr/bin/env python3
"""Safe MetaGPT RAG/tool import diagnostics.

This helper checks imports and optional package availability only. It does not
start vector database services, run web searches, open browsers, download
models, install browser binaries, instantiate provider clients, or call LLMs.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import sys
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Check:
    name: str
    module: str
    advice: str
    mode: str = "import"
    group: str = "core"


CHECKS = [
    Check(
        group="core",
        name="MetaGPT package",
        module="metagpt",
        advice="Install MetaGPT in the active Python environment.",
    ),
    Check(
        group="core",
        name="RAG interface",
        module="metagpt.rag.interface",
        advice="Base MetaGPT should expose metagpt.rag.interface; reinstall MetaGPT if missing.",
    ),
    Check(
        group="rag",
        name="RAG schema",
        module="metagpt.rag.schema",
        advice="Install RAG dependencies, especially chromadb and llama-index-core, or install metagpt[rag].",
    ),
    Check(
        group="rag",
        name="SimpleEngine",
        module="metagpt.rag.engines.simple",
        advice="Install metagpt[rag] and configure embedding/LLM providers before constructing engines.",
    ),
    Check(
        group="rag",
        name="Retriever factory",
        module="metagpt.rag.factories.retriever",
        advice="Install vector-store dependencies for the selected retriever, such as faiss/chromadb/Elasticsearch LlamaIndex integrations.",
    ),
    Check(
        group="rag",
        name="Ranker factory",
        module="metagpt.rag.factories.ranker",
        advice="Install optional reranker packages only for selected rankers, or omit ranker_configs.",
    ),
    Check(
        group="rag",
        name="LlamaIndex core",
        module="llama_index.core",
        mode="spec",
        advice="Install llama-index-core or metagpt[rag].",
    ),
    Check(
        group="rag",
        name="LlamaIndex file readers",
        module="llama_index.readers.file",
        mode="spec",
        advice="Install llama-index-readers-file when loading PDFs/docx/other file formats through SimpleDirectoryReader.",
    ),
    Check(
        group="vector-stores",
        name="FAISS Python package",
        module="faiss",
        mode="spec",
        advice="Install a compatible CPU FAISS package for local vector search; use GPU FAISS only when the runtime supports it.",
    ),
    Check(
        group="vector-stores",
        name="LlamaIndex FAISS vector store",
        module="llama_index.vector_stores.faiss",
        mode="spec",
        advice="Install llama-index-vector-stores-faiss or metagpt[rag].",
    ),
    Check(
        group="vector-stores",
        name="ChromaDB",
        module="chromadb",
        mode="spec",
        advice="Install chromadb for Chroma retriever/index configs and RAG schema imports.",
    ),
    Check(
        group="vector-stores",
        name="LlamaIndex Chroma vector store",
        module="llama_index.vector_stores.chroma",
        mode="spec",
        advice="Install llama-index-vector-stores-chroma or metagpt[rag].",
    ),
    Check(
        group="vector-stores",
        name="LlamaIndex Elasticsearch vector store",
        module="llama_index.vector_stores.elasticsearch",
        mode="spec",
        advice="Install llama-index-vector-stores-elasticsearch and verify Elasticsearch service credentials separately.",
    ),
    Check(
        group="vector-stores",
        name="Qdrant client",
        module="qdrant_client",
        mode="spec",
        advice="Install qdrant-client only when using QdrantStore; verify server/cloud reachability separately.",
    ),
    Check(
        group="vector-stores",
        name="Milvus client",
        module="pymilvus",
        mode="spec",
        advice="Install pymilvus only when using MilvusStore; provide MilvusConnection.uri/token separately.",
    ),
    Check(
        group="vector-stores",
        name="LanceDB",
        module="lancedb",
        mode="spec",
        advice="Install lancedb with a PyArrow version compatible with the active Python environment.",
    ),
    Check(
        group="search",
        name="SearchEngine dispatcher",
        module="metagpt.tools.search_engine",
        advice="SearchEngine imports metagpt.tools, which registers tool libraries; install base tool dependencies such as numpy/pandas/sklearn if this import fails before provider selection.",
    ),
    Check(
        group="search",
        name="DuckDuckGo search package",
        module="duckduckgo_search",
        mode="spec",
        advice="Install metagpt[search-ddg] for DuckDuckGo search; network access is still required.",
    ),
    Check(
        group="search",
        name="Google API client",
        module="googleapiclient.discovery",
        mode="spec",
        advice="Install metagpt[search-google] and provide both api_key and cse_id for direct Google search.",
    ),
    Check(
        group="search",
        name="aiohttp",
        module="aiohttp",
        mode="spec",
        advice="Install aiohttp for Serper, SerpAPI, and Bing async HTTP wrappers.",
    ),
    Check(
        group="search",
        name="MeiliSearch client",
        module="meilisearch",
        mode="spec",
        advice="Install meilisearch only when using MetaGPT MeiliSearch tools; service startup is a separate prerequisite.",
    ),
    Check(
        group="browser",
        name="WebBrowserEngine dispatcher",
        module="metagpt.tools.web_browser_engine",
        advice="WebBrowserEngine imports metagpt.tools, which registers tool libraries; install base tool dependencies if this fails, then add Playwright or Selenium extras for the selected wrapper.",
    ),
    Check(
        group="browser",
        name="Playwright package",
        module="playwright.async_api",
        mode="spec",
        advice="Install playwright and browser binaries with user approval before browser automation.",
    ),
    Check(
        group="browser",
        name="Selenium package",
        module="selenium",
        mode="spec",
        advice="Install metagpt[selenium] and ensure compatible browser/WebDriver availability.",
    ),
    Check(
        group="browser",
        name="webdriver-manager",
        module="webdriver_manager",
        mode="spec",
        advice="Install webdriver_manager or pass an explicit Selenium executable_path.",
    ),
    Check(
        group="registry",
        name="Tool data models",
        module="metagpt.tools.tool_data_type",
        advice="Tool data model import can trigger metagpt.tools library registration; install base data/tool dependencies such as numpy, pandas, and scikit-learn if it fails.",
    ),
    Check(
        group="registry",
        name="Tool registry",
        module="metagpt.tools.tool_registry",
        advice="ToolRegistry import can trigger metagpt.tools library registration; avoid broad unsafe path scans and install base tool dependencies if registration imports fail.",
    ),
    Check(
        group="registry",
        name="Tool recommendation",
        module="metagpt.tools.tool_recommend",
        advice="Install numpy, rank_bm25, pandas/sklearn-style dependencies as needed; LLM ranking requires configured MetaGPT LLM.",
    ),
    Check(
        group="registry",
        name="rank_bm25",
        module="rank_bm25",
        mode="spec",
        advice="Install rank_bm25 for BM25ToolRecommender and BM25 retrieval paths.",
    ),
    Check(
        group="registry",
        name="NumPy",
        module="numpy",
        mode="spec",
        advice="Install numpy for BM25ToolRecommender and data tooling.",
    ),
    Check(
        group="tools",
        name="Registered tool libs",
        module="metagpt.tools.libs",
        advice="Tool library import registers built-ins; failures usually mean missing browser/data/ML optional packages.",
    ),
    Check(
        group="tools",
        name="Editor tool",
        module="metagpt.tools.libs.editor",
        advice="Editor import should work in base installs; similarity_search additionally needs RAG dependencies.",
    ),
    Check(
        group="tools",
        name="Data preprocess tools",
        module="metagpt.tools.libs.data_preprocess",
        advice="Install pandas, numpy, and scikit-learn-compatible packages for data preprocessing tools.",
    ),
    Check(
        group="tools",
        name="Feature engineering tools",
        module="metagpt.tools.libs.feature_engineering",
        advice="Install pandas/numpy/scikit-learn; some tree-based functions may need extra ML libraries.",
    ),
]

GROUP_ALIASES = {
    "all": sorted({check.group for check in CHECKS}),
    "core": ["core"],
    "rag": ["core", "rag"],
    "vector-stores": ["vector-stores"],
    "docstores": ["vector-stores"],
    "search": ["search"],
    "browser": ["browser"],
    "registry": ["registry"],
    "tools": ["registry", "tools"],
}


def find_check(name: str) -> Check | None:
    for check in CHECKS:
        if check.name == name:
            return check
    return None


def selected_checks(groups: Iterable[str], names: Iterable[str]) -> list[Check]:
    selected_groups: set[str] = set()
    for group in groups:
        if group not in GROUP_ALIASES:
            raise SystemExit(f"Unknown group {group!r}. Available groups: {', '.join(sorted(GROUP_ALIASES))}")
        selected_groups.update(GROUP_ALIASES[group])

    checks = [check for check in CHECKS if check.group in selected_groups]
    for name in names:
        match = find_check(name)
        if not match:
            raise SystemExit(f"Unknown check name {name!r}. Use --list to see available names.")
        checks.append(match)

    deduped: list[Check] = []
    seen: set[tuple[str, str]] = set()
    for check in checks:
        key = (check.group, check.name)
        if key not in seen:
            deduped.append(check)
            seen.add(key)
    return deduped


def run_check(check: Check) -> tuple[bool, str]:
    try:
        if check.mode == "spec":
            spec = importlib.util.find_spec(check.module)
            if spec is None:
                return False, "module spec not found"
            return True, "module spec found"
        importlib.import_module(check.module)
        return True, "import ok"
    except Exception as exc:  # noqa: BLE001 - diagnostics should report any import-time failure.
        return False, f"{exc.__class__.__name__}: {exc}"


def print_checks(checks: list[Check]) -> int:
    print("MetaGPT RAG/tool import diagnostics")
    print("No services, searches, browsers, model downloads, or LLM calls will be started.\n")

    failures = 0
    for check in checks:
        ok, detail = run_check(check)
        status = "OK" if ok else "MISSING"
        print(f"[{status}] {check.group}: {check.name} ({check.module})")
        print(f"       {detail}")
        if not ok:
            failures += 1
            print(f"       advice: {check.advice}")
    print()
    if failures:
        print(f"Completed with {failures} missing or failing check(s).")
        return 1
    print("All selected checks passed.")
    return 0


def list_checks() -> None:
    print("Groups:")
    for group in sorted(GROUP_ALIASES):
        print(f"  {group}: {', '.join(GROUP_ALIASES[group])}")
    print("\nChecks:")
    for check in CHECKS:
        print(f"  {check.group}: {check.name} -> {check.module} [{check.mode}]")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--group",
        action="append",
        default=[],
        help="Check group to run. Repeatable. Common values: rag, vector-stores, search, browser, registry, tools, all.",
    )
    parser.add_argument(
        "--check",
        action="append",
        default=[],
        help="Run one named check in addition to selected groups. Repeatable; use --list for names.",
    )
    parser.add_argument("--all", action="store_true", help="Run every check.")
    parser.add_argument("--list", action="store_true", help="List available groups/checks and exit.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Reserved for future machine-readable output; currently rejected to avoid implying a stable schema.",
    )
    args = parser.parse_args(argv)
    if args.json:
        parser.error("--json is not implemented; use text output.")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.list:
        list_checks()
        return 0

    groups = args.group or []
    if args.all:
        groups = ["all"]
    if not groups and not args.check:
        groups = ["core"]

    checks = selected_checks(groups, args.check)
    return print_checks(checks)


if __name__ == "__main__":
    raise SystemExit(main())
