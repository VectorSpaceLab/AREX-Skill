#!/usr/bin/env python3
"""Check CrewAI memory, knowledge, RAG, and loader imports safely.

This diagnostic imports selected CrewAI modules and reports whether core and
optional retrieval components are available. It does not instantiate LLMs,
embedding providers, vector clients, tools, loaders, database connections, or
network-backed resources. It performs no network calls, credential reads beyond
ordinary import side effects, file mutation, or destructive reset operations.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import asdict, dataclass
from importlib import metadata
from typing import Iterable


@dataclass(frozen=True)
class ImportCheck:
    """Result for one import target."""

    group: str
    name: str
    module: str
    required: bool
    ok: bool
    detail: str


CORE_IMPORTS: tuple[tuple[str, str, str], ...] = (
    ("memory", "Memory", "crewai.memory.unified_memory"),
    ("memory", "MemoryScope/MemorySlice", "crewai.memory.memory_scope"),
    ("memory", "Memory storage factory", "crewai.memory.storage.factory"),
    ("knowledge", "Knowledge", "crewai.knowledge.knowledge"),
    ("knowledge", "StringKnowledgeSource", "crewai.knowledge.source.string_knowledge_source"),
    ("knowledge", "TextFileKnowledgeSource", "crewai.knowledge.source.text_file_knowledge_source"),
    ("knowledge", "KnowledgeStorage", "crewai.knowledge.storage.knowledge_storage"),
    ("rag", "RAG config utilities", "crewai.rag.config.utils"),
    ("rag", "RAG factory", "crewai.rag.factory"),
    ("rag", "Embedding factory", "crewai.rag.embeddings.factory"),
    ("rag", "Embedding types", "crewai.rag.embeddings.types"),
    ("rag", "RAG base client", "crewai.rag.core.base_client"),
    ("rag-tool", "RagTool", "crewai_tools.tools.rag.rag_tool"),
    ("rag-tool", "RagTool types", "crewai_tools.tools.rag.types"),
    ("rag-tool", "CrewAI RAG adapter", "crewai_tools.adapters.crewai_rag_adapter"),
    ("rag-loader", "DataType registry", "crewai_tools.rag.data_types"),
    ("rag-loader", "BaseLoader", "crewai_tools.rag.base_loader"),
)

OPTIONAL_IMPORTS: tuple[tuple[str, str, str], ...] = (
    ("knowledge", "PDFKnowledgeSource", "crewai.knowledge.source.pdf_knowledge_source"),
    ("knowledge", "CSVKnowledgeSource", "crewai.knowledge.source.csv_knowledge_source"),
    ("knowledge", "ExcelKnowledgeSource", "crewai.knowledge.source.excel_knowledge_source"),
    ("knowledge", "JSONKnowledgeSource", "crewai.knowledge.source.json_knowledge_source"),
    ("knowledge", "CrewDoclingSource", "crewai.knowledge.source.crew_docling_source"),
    ("rag-provider", "ChromaDBConfig", "crewai.rag.chromadb.config"),
    ("rag-provider", "QdrantConfig", "crewai.rag.qdrant.config"),
    ("rag-provider", "ChromaDB client", "crewai.rag.chromadb.client"),
    ("rag-provider", "Qdrant client", "crewai.rag.qdrant.client"),
    ("rag-loader", "Text loaders", "crewai_tools.rag.loaders.text_loader"),
    ("rag-loader", "PDF loader", "crewai_tools.rag.loaders.pdf_loader"),
    ("rag-loader", "CSV loader", "crewai_tools.rag.loaders.csv_loader"),
    ("rag-loader", "JSON loader", "crewai_tools.rag.loaders.json_loader"),
    ("rag-loader", "XML loader", "crewai_tools.rag.loaders.xml_loader"),
    ("rag-loader", "DOCX loader", "crewai_tools.rag.loaders.docx_loader"),
    ("rag-loader", "MDX loader", "crewai_tools.rag.loaders.mdx_loader"),
    ("rag-loader", "Directory loader", "crewai_tools.rag.loaders.directory_loader"),
    ("rag-loader", "Web page loader", "crewai_tools.rag.loaders.webpage_loader"),
    ("rag-loader", "Docs site loader", "crewai_tools.rag.loaders.docs_site_loader"),
    ("rag-loader", "GitHub loader", "crewai_tools.rag.loaders.github_loader"),
    ("rag-loader", "YouTube video loader", "crewai_tools.rag.loaders.youtube_video_loader"),
    ("rag-loader", "YouTube channel loader", "crewai_tools.rag.loaders.youtube_channel_loader"),
    ("rag-loader", "MySQL loader", "crewai_tools.rag.loaders.mysql_loader"),
    ("rag-loader", "PostgreSQL loader", "crewai_tools.rag.loaders.postgres_loader"),
)

DISTRIBUTIONS: tuple[str, ...] = (
    "crewai",
    "crewai-cli",
    "crewai-tools",
    "crewai-files",
    "crewai-core",
    "chromadb",
    "qdrant-client",
    "fastembed",
    "lancedb",
    "docling",
    "pdfplumber",
    "pandas",
    "python-docx",
    "PyGithub",
    "youtube-transcript-api",
    "pymysql",
    "psycopg2-binary",
)


def check_import(group: str, name: str, module: str, required: bool) -> ImportCheck:
    """Import one module and return a structured result."""
    try:
        importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - diagnostics must report any import failure.
        return ImportCheck(
            group=group,
            name=name,
            module=module,
            required=required,
            ok=False,
            detail=f"{exc.__class__.__name__}: {exc}",
        )
    return ImportCheck(
        group=group,
        name=name,
        module=module,
        required=required,
        ok=True,
        detail="imported",
    )


def package_versions(distributions: Iterable[str]) -> dict[str, str | None]:
    """Return installed package versions without importing the packages."""
    versions: dict[str, str | None] = {}
    for dist_name in distributions:
        try:
            versions[dist_name] = metadata.version(dist_name)
        except metadata.PackageNotFoundError:
            versions[dist_name] = None
    return versions


def render_table(checks: list[ImportCheck], versions: dict[str, str | None]) -> str:
    """Render human-readable diagnostic output."""
    lines = ["Package versions:"]
    for name, version in versions.items():
        lines.append(f"  {name}: {version or 'not installed'}")

    lines.append("")
    lines.append("Import checks:")
    width_group = max(len(c.group) for c in checks) if checks else 5
    width_name = max(len(c.name) for c in checks) if checks else 4
    for check in checks:
        status = "OK" if check.ok else ("MISSING" if not check.required else "FAIL")
        required = "required" if check.required else "optional"
        lines.append(
            f"  {check.group:<{width_group}}  {check.name:<{width_name}}  "
            f"{required:<8}  {status:<7}  {check.detail}"
        )
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Safely check installed CrewAI memory, knowledge, RAG, vector provider, "
            "and loader imports without network calls or LLM execution."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a table.",
    )
    parser.add_argument(
        "--core-only",
        action="store_true",
        help="Check only core imports and skip optional provider/loader modules.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run import diagnostics."""
    args = parse_args(sys.argv[1:] if argv is None else argv)

    targets = [(group, name, module, True) for group, name, module in CORE_IMPORTS]
    if not args.core_only:
        targets.extend(
            (group, name, module, False) for group, name, module in OPTIONAL_IMPORTS
        )

    checks = [check_import(*target) for target in targets]
    versions = package_versions(DISTRIBUTIONS)

    required_failures = [check for check in checks if check.required and not check.ok]

    if args.json:
        print(
            json.dumps(
                {
                    "ok": not required_failures,
                    "versions": versions,
                    "checks": [asdict(check) for check in checks],
                    "required_failures": [asdict(check) for check in required_failures],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(render_table(checks, versions))
        if required_failures:
            print("\nRequired import failures detected.", file=sys.stderr)

    return 1 if required_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
