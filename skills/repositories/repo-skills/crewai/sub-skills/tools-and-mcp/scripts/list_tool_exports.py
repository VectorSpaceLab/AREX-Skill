#!/usr/bin/env python3
"""List installed crewai_tools exports without instantiating tools or calling APIs.

The script imports the top-level ``crewai_tools`` package, reads public export
names from ``__all__`` when available, applies conservative name-based category
heuristics, and prints either a table or JSON. It does not call LLMs, network
services, credentials, MCP servers, database connections, or destructive file
operations.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from importlib import metadata
from typing import Iterable


@dataclass(frozen=True)
class ToolExport:
    """One public export and its inferred category."""

    name: str
    category: str


CATEGORY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "mcp",
        ("MCP",),
    ),
    (
        "file-document",
        (
            "File",
            "Directory",
            "CSV",
            "DOCX",
            "JSON",
            "MDX",
            "PDF",
            "TXT",
            "XML",
            "OCR",
            "Compressor",
        ),
    ),
    (
        "web-scraping",
        (
            "Scrape",
            "Crawler",
            "Crawl",
            "Browser",
            "Firecrawl",
            "BrightData",
            "Oxylabs",
            "Selenium",
            "Spider",
            "Stagehand",
            "Hyperbrowser",
            "Jina",
            "Scrapfly",
        ),
    ),
    (
        "search-research",
        (
            "Search",
            "Serper",
            "SerpApi",
            "Serply",
            "Tavily",
            "Brave",
            "Exa",
            "Github",
            "Arxiv",
            "Linkup",
            "Youtube",
            "YouTube",
            "CodeDocs",
            "Website",
        ),
    ),
    (
        "database-data",
        (
            "MySQL",
            "SQL",
            "Snowflake",
            "SingleStore",
            "MongoDB",
            "Qdrant",
            "Weaviate",
            "Couchbase",
            "Databricks",
            "Vector",
        ),
    ),
    (
        "cloud-storage",
        ("S3", "Bedrock", "AWS"),
    ),
    (
        "automation-integration",
        (
            "Zapier",
            "Composio",
            "Apify",
            "MultiOn",
            "CrewaiPlatform",
            "Automation",
            "Enterprise",
            "Action",
            "MergeAgent",
            "InvokeCrewAI",
            "GenerateCrewai",
        ),
    ),
    (
        "ai-ml-sandbox",
        (
            "DallE",
            "Dall",
            "Vision",
            "LlamaIndex",
            "Rag",
            "RAG",
            "Daytona",
            "E2B",
            "Patronus",
            "ContextualAI",
            "AIMind",
        ),
    ),
)


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""

    parser = argparse.ArgumentParser(
        description=(
            "Safely list public exports from the installed crewai_tools package "
            "without instantiating tools or making external calls."
        )
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format. Defaults to table.",
    )
    parser.add_argument(
        "--category",
        help="Only show exports in this inferred category, such as file-document or mcp.",
    )
    parser.add_argument(
        "--include-private",
        action="store_true",
        help=(
            "Fall back to non-underscore module attributes if __all__ is missing. "
            "Normally only __all__ exports are listed."
        ),
    )
    return parser.parse_args()


def infer_category(name: str) -> str:
    """Infer a practical category from an export name."""

    for category, markers in CATEGORY_RULES:
        if any(marker in name for marker in markers):
            return category
    return "other"


def package_version(distribution: str) -> str | None:
    """Return an installed package version if metadata is available."""

    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def load_export_names(include_private: bool) -> list[str]:
    """Import crewai_tools and return candidate export names."""

    try:
        module = importlib.import_module("crewai_tools")
    except ImportError as exc:
        raise SystemExit(
            "Could not import crewai_tools. Install CrewAI tools first, for example: "
            "pip install 'crewai[tools]'. Original import error: "
            f"{exc}"
        ) from exc

    explicit_exports = getattr(module, "__all__", None)
    if explicit_exports:
        return sorted(str(name) for name in explicit_exports)

    if include_private:
        return sorted(name for name in dir(module) if not name.startswith("_"))

    return []


def build_exports(names: Iterable[str], category_filter: str | None) -> list[ToolExport]:
    """Build categorized export records."""

    exports = [ToolExport(name=name, category=infer_category(name)) for name in names]
    if category_filter:
        exports = [export for export in exports if export.category == category_filter]
    return exports


def print_table(exports: list[ToolExport], version: str | None) -> None:
    """Print a human-readable grouped table."""

    print(f"crewai_tools version: {version or 'unknown'}")
    print(f"exports listed: {len(exports)}")
    print()

    grouped: dict[str, list[str]] = defaultdict(list)
    for export in exports:
        grouped[export.category].append(export.name)

    for category in sorted(grouped):
        print(f"[{category}] ({len(grouped[category])})")
        for name in grouped[category]:
            print(f"  - {name}")
        print()


def print_json(exports: list[ToolExport], version: str | None) -> None:
    """Print JSON output for automated checks."""

    payload = {
        "package": "crewai_tools",
        "version": version,
        "count": len(exports),
        "exports": [asdict(export) for export in exports],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def main() -> int:
    """Run the export listing command."""

    args = parse_args()
    names = load_export_names(include_private=args.include_private)
    exports = build_exports(names, category_filter=args.category)
    version = package_version("crewai-tools") or package_version("crewai_tools")

    if args.format == "json":
        print_json(exports, version)
    else:
        print_table(exports, version)

    if args.category and not exports:
        print(f"No exports matched category: {args.category}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
