#!/usr/bin/env python3
"""Run a safe text-to-brain and QA smoke using fake local components by default."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import tempfile
from pathlib import Path
from uuid import uuid4

os.environ.setdefault("OPENAI_API_KEY", "test")

from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models import FakeListChatModel

from quivr_core import Brain
from quivr_core.files.file import load_qfile
from quivr_core.llm import LLMEndpoint
from quivr_core.processor.implementations.simple_txt_processor import (
    SimpleTxtProcessor,
)
from quivr_core.processor.splitter import SplitterConfig
from quivr_core.rag.entities.config import LLMEndpointConfig
from quivr_core.storage.local_storage import TransparentStorage

DEFAULT_TEXT = (
    "Quivr builds a brain from documents and answers questions with RAG. "
    "Gold is a yellow metal that many people use as a simple retrieval target."
)
DEFAULT_QUESTION = "What is gold?"
DEFAULT_SEARCH_QUERY = "gold"
FAKE_RESPONSES = ["smoke answer"] * 20


async def build_brain(text: str, chunk_size: int, chunk_overlap: int) -> tuple[Brain, list]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as temp_file:
        temp_file.write(text)
        temp_path = Path(temp_file.name)

    try:
        brain_id = uuid4()
        qfile = await load_qfile(brain_id, temp_path)
        processor = SimpleTxtProcessor(
            splitter_config=SplitterConfig(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        )
        processed = await processor.process_file(qfile)
        chunks = processed.chunks

        embedder = DeterministicFakeEmbedding(size=20)
        llm = LLMEndpoint(
            llm=FakeListChatModel(responses=FAKE_RESPONSES),
            llm_config=LLMEndpointConfig(
                model="test",
                llm_base_url="local",
                llm_api_key="test",
            ),
        )
        brain = await Brain.afrom_langchain_documents(
            name="smoke_brain",
            langchain_documents=chunks,
            storage=TransparentStorage(),
            llm=llm,
            embedder=embedder,
        )
        return brain, chunks
    finally:
        temp_path.unlink(missing_ok=True)


async def run_ingestion_phase(brain: Brain, chunks: list) -> dict[str, object]:
    return {
        "brain_name": brain.name,
        "brain_id": str(brain.id),
        "chunk_count": len(chunks),
        "first_chunk_preview": chunks[0].page_content[:80] if chunks else "",
        "storage_type": type(brain.storage).__name__ if brain.storage else None,
    }


async def run_qa_phase(
    brain: Brain,
    question: str,
    search_query: str,
    stream: bool,
) -> dict[str, object]:
    results: dict[str, object] = {}

    search_hits = await brain.asearch(search_query, n_results=1)
    results["search_hit_count"] = len(search_hits)
    if search_hits:
        results["top_search_distance"] = search_hits[0].distance
        results["top_search_preview"] = search_hits[0].chunk.page_content[:80]

    answer = await brain.aask(run_id=uuid4(), question=question)
    results["answer"] = answer.answer
    results["answer_metadata_sources"] = len(answer.metadata.sources) if answer.metadata else 0

    if stream:
        streamed_answer = ""
        streamed_chunks = 0
        last_metadata = None
        async for chunk in brain.ask_streaming(run_id=uuid4(), question=question):
            if chunk.answer:
                streamed_answer += chunk.answer
                streamed_chunks += 1
            if chunk.last_chunk:
                last_metadata = {
                    "citations": chunk.metadata.citations,
                    "followup_questions": chunk.metadata.followup_questions,
                    "source_count": len(chunk.metadata.sources),
                }
        results["stream_answer"] = streamed_answer
        results["stream_chunk_count"] = streamed_chunks
        results["stream_metadata"] = last_metadata

    results["chat_history_length"] = len(brain.default_chat)
    return results


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        choices=("ingestion", "qa", "both"),
        default="both",
        help="Which smoke phase to run.",
    )
    parser.add_argument(
        "--text",
        default=DEFAULT_TEXT,
        help="Plain text to load into the smoke brain.",
    )
    parser.add_argument(
        "--text-file",
        type=Path,
        help="Optional text file to use instead of the built-in text.",
    )
    parser.add_argument(
        "--question",
        default=DEFAULT_QUESTION,
        help="Question to ask the smoke brain.",
    )
    parser.add_argument(
        "--search-query",
        default=DEFAULT_SEARCH_QUERY,
        help="Retrieval query used for the search smoke.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=400,
        help="Chunk size passed to SplitterConfig.",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=100,
        help="Chunk overlap passed to SplitterConfig.",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Also exercise Brain.ask_streaming.",
    )
    args = parser.parse_args()

    text = args.text_file.read_text(encoding="utf-8") if args.text_file else args.text
    brain, chunks = await build_brain(text, args.chunk_size, args.chunk_overlap)

    summary: dict[str, object] = {"phase": args.phase}

    if args.phase in {"ingestion", "both"}:
        summary["ingestion"] = await run_ingestion_phase(brain, chunks)

    if args.phase in {"qa", "both"}:
        summary["qa"] = await run_qa_phase(
            brain,
            question=args.question,
            search_query=args.search_query,
            stream=args.stream,
        )

    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
