#!/usr/bin/env python3
"""Read-only import smoke checks for langchain-classic legacy surfaces."""

from __future__ import annotations

import argparse
import importlib
import sys
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ImportCheck:
    """One import check for a module and optional attribute."""

    module: str
    attribute: str | None = None
    optional: bool = False


REQUIRED_CHECKS: tuple[ImportCheck, ...] = (
    ImportCheck("langchain_classic"),
    ImportCheck("langchain_classic.chains", "LLMChain"),
    ImportCheck("langchain_classic.chains.conversational_retrieval.base", "ConversationalRetrievalChain"),
    ImportCheck("langchain_classic.chains.combine_documents.stuff", "StuffDocumentsChain"),
    ImportCheck("langchain_classic.agents", "AgentExecutor"),
    ImportCheck("langchain_classic.agents.initialize", "initialize_agent"),
    ImportCheck("langchain_classic.retrievers", "MultiVectorRetriever"),
    ImportCheck("langchain_classic.retrievers", "ParentDocumentRetriever"),
    ImportCheck("langchain_classic.document_loaders", "TextLoader"),
    ImportCheck("langchain_classic.document_transformers", "LongContextReorder"),
    ImportCheck("langchain_classic.memory", "ConversationBufferMemory"),
    ImportCheck("langchain_classic.evaluation", "load_evaluator"),
    ImportCheck("langchain_classic.callbacks", "StdOutCallbackHandler"),
    ImportCheck("langchain_classic.schema", "Document"),
)

OPTIONAL_CHECKS: tuple[ImportCheck, ...] = (
    ImportCheck("langchain_classic.retrievers", "PubMedRetriever", optional=True),
    ImportCheck("langchain_classic.retrievers", "WikipediaRetriever", optional=True),
    ImportCheck("langchain_classic.retrievers", "BM25Retriever", optional=True),
    ImportCheck("langchain_classic.retrievers", "WeaviateHybridSearchRetriever", optional=True),
)


def _import_check(check: ImportCheck) -> tuple[bool, str]:
    try:
        module = importlib.import_module(check.module)
        if check.attribute is not None:
            getattr(module, check.attribute)
    except Exception as exc:  # noqa: BLE001
        label = f"{check.module}:{check.attribute}" if check.attribute else check.module
        return False, f"FAIL {label} -> {type(exc).__name__}: {exc}"
    label = f"{check.module}:{check.attribute}" if check.attribute else check.module
    return True, f"OK   {label}"


def run_checks(include_optional: bool) -> int:
    """Run import checks and return a process exit code."""
    checks: tuple[ImportCheck, ...]
    checks = REQUIRED_CHECKS + (OPTIONAL_CHECKS if include_optional else ())
    failures: list[str] = []

    for check in checks:
        passed, message = _import_check(check)
        print(message)
        if not passed and not check.optional:
            failures.append(message)
        elif not passed and check.optional:
            print("SKIP optional dependency may be absent; investigate only if required.")

    if failures:
        print("\nRequired import checks failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-optional",
        action="store_true",
        help="Also try common optional community/provider re-export imports.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the smoke checker."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_checks(include_optional=args.include_optional)


if __name__ == "__main__":
    raise SystemExit(main())
