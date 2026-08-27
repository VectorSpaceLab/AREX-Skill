#!/usr/bin/env python3
"""No-network smoke checks for DeepSearcher RAG agents.

This helper instantiates mock LLM, embedding, and vector DB objects, then checks
return shapes for NaiveRAG or DeepSearch. It does not read DeepSearcher source
repo tests, does not contact network services, and does not require credentials.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List


class ImportProblem(RuntimeError):
    """Raised when DeepSearcher is unavailable in the active environment."""


try:
    from deepsearcher.agent import DeepSearch, NaiveRAG
    from deepsearcher.embedding.base import BaseEmbedding
    from deepsearcher.llm.base import BaseLLM, ChatResponse
    from deepsearcher.vector_db.base import BaseVectorDB, CollectionInfo, RetrievalResult
except Exception as exc:  # pragma: no cover - message path for user environments
    raise ImportProblem(
        "DeepSearcher must be installed in the active environment to run this helper."
    ) from exc


class MockLLM(BaseLLM):
    """Prompt-sensitive deterministic LLM mock for RAG return-shape checks."""

    def __init__(self, *, noisy_router: bool = False) -> None:
        self.noisy_router = noisy_router
        self.calls: List[str] = []

    def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> ChatResponse:
        content = messages[0]["content"] if messages else ""
        self.calls.append(content)

        if "collection_name" in content and "COLLECTION_INFO" in content:
            response = '["kb"]'
        elif "break down the original question" in content or "Original Question:" in content:
            response = '["What does the knowledge base say about renewal risk?"]'
        elif "Is the chunk helpful" in content:
            response = "YES"
        elif "Respond exclusively in valid List" in content:
            response = "[]"
        elif "Given a list of agent indexes" in content:
            response = "I recommend agent 1" if self.noisy_router else "1"
        elif "select the ones that are support" in content:
            response = "[0]"
        elif "judge whether you have enough information" in content:
            response = "Yes"
        elif "generate a new simple follow-up question" in content:
            response = "What evidence mentions renewal risk?"
        else:
            response = "Mock answer: renewal risk appears in the bundled mock knowledge base."

        return ChatResponse(content=response, total_tokens=max(1, len(content) // 80 + 1))


class MockEmbedding(BaseEmbedding):
    """Deterministic embedding mock."""

    @property
    def dimension(self) -> int:
        return 4

    def embed_query(self, text: str) -> List[float]:
        base = float(len(text) % 7)
        return [base, base + 0.1, base + 0.2, base + 0.3]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_query(text) for text in texts]


class MockVectorDB(BaseVectorDB):
    """In-memory vector DB mock with one or two collections."""

    def __init__(self, *, empty: bool = False, two_collections: bool = False) -> None:
        super().__init__(default_collection="kb")
        self.empty = empty
        self.two_collections = two_collections
        self.search_calls: List[Dict[str, Any]] = []

    def init_collection(
        self,
        dim: int,
        collection: str,
        description: str,
        force_new_collection: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        return None

    def insert_data(self, collection: str, chunks: List[Any], *args: Any, **kwargs: Any) -> None:
        return None

    def list_collections(self, *args: Any, **kwargs: Any) -> List[CollectionInfo]:
        if self.empty:
            return []
        infos = [CollectionInfo("kb", "Mock knowledge base about renewal risk")]
        if self.two_collections:
            infos.append(CollectionInfo("archive", "Older unrelated archive"))
        return infos

    def search_data(
        self, collection: str, vector: List[float], *args: Any, **kwargs: Any
    ) -> List[RetrievalResult]:
        self.search_calls.append(
            {
                "collection": collection,
                "top_k": kwargs.get("top_k"),
                "query_text": kwargs.get("query_text"),
            }
        )
        if self.empty:
            return []
        top_k = int(kwargs.get("top_k") or 3)
        rows = [
            RetrievalResult(
                embedding=vector,
                text="Renewal risk is highest when approval dates are missing.",
                reference=f"{collection}:policy-note-1",
                metadata={"wider_text": "Policy note: Renewal risk is highest when approval dates are missing."},
                score=0.91,
            ),
            RetrievalResult(
                embedding=vector,
                text="Escalate renewals with unclear owner assignments.",
                reference=f"{collection}:policy-note-2",
                metadata={},
                score=0.82,
            ),
        ]
        return rows[:top_k]

    def clear_db(self, *args: Any, **kwargs: Any) -> None:
        return None


def _result_summary(answer: str, refs: List[RetrievalResult], tokens: int, vector_db: MockVectorDB, llm: MockLLM) -> Dict[str, Any]:
    return {
        "answer_type": type(answer).__name__,
        "answer_preview": answer[:120],
        "refs_type": type(refs).__name__,
        "ref_count": len(refs),
        "ref_fields_ok": all(
            all(hasattr(ref, attr) for attr in ("embedding", "text", "reference", "metadata", "score"))
            for ref in refs
        ),
        "tokens_type": type(tokens).__name__,
        "tokens": tokens,
        "search_calls": vector_db.search_calls,
        "llm_calls": len(llm.calls),
    }


def run_naive(args: argparse.Namespace) -> Dict[str, Any]:
    llm = MockLLM()
    embedding = MockEmbedding()
    vector_db = MockVectorDB(empty=args.empty, two_collections=args.two_collections)
    agent = NaiveRAG(
        llm=llm,
        embedding_model=embedding,
        vector_db=vector_db,
        top_k=args.top_k,
        route_collection=True,
        text_window_splitter=not args.no_wider_text,
    )
    answer, refs, tokens = agent.query(args.query)
    summary = _result_summary(answer, refs, tokens, vector_db, llm)
    summary["agent"] = "naive"
    summary["checks_passed"] = isinstance(answer, str) and isinstance(refs, list) and isinstance(tokens, int)
    return summary


def run_deep_search(args: argparse.Namespace) -> Dict[str, Any]:
    llm = MockLLM()
    embedding = MockEmbedding()
    vector_db = MockVectorDB(empty=args.empty, two_collections=args.two_collections)
    agent = DeepSearch(
        llm=llm,
        embedding_model=embedding,
        vector_db=vector_db,
        max_iter=args.max_iter,
        route_collection=True,
        text_window_splitter=not args.no_wider_text,
    )
    answer, refs, tokens = agent.query(args.query, max_iter=args.max_iter)
    summary = _result_summary(answer, refs, tokens, vector_db, llm)
    summary["agent"] = "deep-search"
    summary["checks_passed"] = isinstance(answer, str) and isinstance(refs, list) and isinstance(tokens, int)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run no-network mock smoke checks for DeepSearcher NaiveRAG or DeepSearch return shapes."
    )
    parser.add_argument("--agent", choices=["naive", "deep-search"], default="naive", help="Agent to instantiate.")
    parser.add_argument("--query", default="What renewal risk is documented?", help="Query string for the mock run.")
    parser.add_argument("--max-iter", type=int, default=1, help="DeepSearch max_iter; keep small for smoke checks.")
    parser.add_argument("--top-k", type=int, default=4, help="NaiveRAG top_k for the mock run.")
    parser.add_argument("--empty", action="store_true", help="Use an empty mock vector DB to exercise no-result behavior.")
    parser.add_argument("--two-collections", action="store_true", help="Expose two mock collections to exercise CollectionRouter.")
    parser.add_argument("--no-wider-text", action="store_true", help="Disable text_window_splitter behavior.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format.")
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    summary = run_naive(args) if args.agent == "naive" else run_deep_search(args)

    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"agent: {summary['agent']}")
        print(f"checks_passed: {summary['checks_passed']}")
        print(f"answer_type: {summary['answer_type']}")
        print(f"ref_count: {summary['ref_count']}")
        print(f"ref_fields_ok: {summary['ref_fields_ok']}")
        print(f"tokens: {summary['tokens']}")
        print(f"llm_calls: {summary['llm_calls']}")
        print(f"search_calls: {summary['search_calls']}")
        print(f"answer_preview: {summary['answer_preview']}")

    return 0 if summary["checks_passed"] else 1


if __name__ == "__main__":  # pragma: no cover
    try:
        raise SystemExit(main())
    except ImportProblem as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
