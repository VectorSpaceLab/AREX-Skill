#!/usr/bin/env python3
"""No-network PaperQA Docs/Doc/Text object smoke.

This script intentionally avoids local files, URLs, live metadata providers,
embeddings, and LLM calls. It proves that the installed PaperQA Python API can
construct core objects and run a structural evidence path over pre-chunked text.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict, dataclass
from typing import Any

from paperqa import Doc, Docs, Settings, Text


class NoNetworkLLM:
    """Sentinel LLM object: any real provider call is a smoke failure."""

    async def call_single(self, *args: Any, **kwargs: Any) -> Any:  # noqa: ARG002
        raise RuntimeError("No-network smoke unexpectedly attempted an LLM call")


class NoNetworkEmbedding:
    """Sentinel embedding object: any real embedding call is a smoke failure."""

    async def embed_documents(self, *args: Any, **kwargs: Any) -> Any:  # noqa: ARG002
        raise RuntimeError("No-network smoke unexpectedly attempted an embedding call")


@dataclass
class SmokeResult:
    ok: bool
    package: str
    docs_count: int
    texts_count: int
    contexts_count: int
    duplicate_add_returned: bool
    first_context_score: int | None
    empty_query_answer: str


async def run_smoke() -> SmokeResult:
    """Run a no-network structural smoke over PaperQA RAG objects."""
    # `defer_embedding` prevents eager embedding during aadd_texts. The answer
    # settings below make aget_evidence summarize by returning raw chunk text
    # and skip vector retrieval, so the sentinels are never invoked.
    settings = Settings(
        parsing={"defer_embedding": True, "use_doc_details": False},
        answer={"evidence_retrieval": False, "evidence_skip_summary": True},
    )

    doc = Doc(
        docname="agenticRagSmoke2024",
        dockey="agentic-rag-smoke-doc",
        citation="Agentic RAG Smoke, 2024",
    )
    texts = [
        Text(
            text="Alpha evidence says PaperQA can store pre-chunked text.",
            name="agenticRagSmoke2024 chunk 1",
            doc=doc,
        ),
        Text(
            text="Beta evidence says deferred embeddings avoid provider calls at ingest.",
            name="agenticRagSmoke2024 chunk 2",
            doc=doc,
        ),
    ]

    docs = Docs(name="agentic-rag-smoke")
    added = await docs.aadd_texts(texts=texts, doc=doc, settings=settings)
    if not added:
        raise AssertionError("Expected first aadd_texts call to add the document")

    duplicate_added = await docs.aadd_texts(texts=texts, doc=doc, settings=settings)
    if duplicate_added:
        raise AssertionError("Expected duplicate aadd_texts call to return False")

    session = await docs.aget_evidence(
        "What does the smoke document say?",
        settings=settings,
        embedding_model=NoNetworkEmbedding(),
        summary_llm_model=NoNetworkLLM(),
    )
    if len(session.contexts) != len(texts):
        raise AssertionError(
            f"Expected {len(texts)} contexts from raw texts, got {len(session.contexts)}"
        )
    if not all(context.context for context in session.contexts):
        raise AssertionError("Expected every smoke context to have text")

    empty_session = await Docs().aquery(
        "Can an empty Docs object answer?",
        settings=settings,
        llm_model=NoNetworkLLM(),
        summary_llm_model=NoNetworkLLM(),
        embedding_model=NoNetworkEmbedding(),
    )
    if not empty_session.answer:
        raise AssertionError("Expected empty aquery to produce a no-answer message")

    try:
        import paperqa

        version = paperqa.__version__
    except Exception:  # pragma: no cover - defensive only
        version = "unknown"

    return SmokeResult(
        ok=True,
        package=f"paperqa=={version}",
        docs_count=len(docs.docs),
        texts_count=len(docs.texts),
        contexts_count=len(session.contexts),
        duplicate_add_returned=duplicate_added,
        first_context_score=session.contexts[0].score if session.contexts else None,
        empty_query_answer=empty_session.answer,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run safe no-network PaperQA Docs/Doc/Text object smokes for the "
            "agentic-rag sub-skill."
        )
    )
    subparsers = parser.add_subparsers(dest="command")

    smoke = subparsers.add_parser(
        "smoke",
        help="construct PaperQA objects and run structural evidence checks without network",
    )
    smoke.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of a concise text summary",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command != "smoke":
        parser.print_help()
        return 0

    result = asyncio.run(run_smoke())
    if args.json:
        print(json.dumps(asdict(result), indent=2, sort_keys=True))
    else:
        print(
            "ok={ok} package={package} docs={docs_count} texts={texts_count} "
            "contexts={contexts_count} duplicate_add_returned={duplicate_add_returned}".format(
                **asdict(result)
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
