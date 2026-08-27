#!/usr/bin/env python3
"""Safe no-network smoke test for nano-graphrag core workflows.

The default run uses a temporary working directory, deterministic fake embedding,
a fake LLM, and a fake entity-extraction function. It performs no network calls,
starts no services, downloads nothing, and does not delete user files.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate nano-graphrag core import, chunking, query-mode guards, insert/query, and reload without network calls."
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=None,
        help="Optional working directory for GraphRAG artifacts. Defaults to a temporary directory that is removed after success.",
    )
    parser.add_argument(
        "--keep-work-dir",
        action="store_true",
        help="Keep the automatically created temporary working directory and print its path. Ignored when --work-dir is supplied.",
    )
    parser.add_argument(
        "--skip-insert",
        action="store_true",
        help="Only check imports, GraphRAG construction, chunking, and query-mode guards; skip insert/query/reload.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print additional progress information.",
    )
    return parser.parse_args()


def _fail(message: str) -> int:
    print(f"core_smoke failed: {message}", file=sys.stderr)
    return 1


def _import_core() -> dict[str, Any]:
    try:
        import numpy as np
        import nano_graphrag
        from nano_graphrag import GraphRAG, QueryParam
        from nano_graphrag._op import chunking_by_seperators, chunking_by_token_size, get_chunks
        from nano_graphrag._utils import compute_mdhash_id, wrap_embedding_func_with_attrs
        from nano_graphrag.prompt import GRAPH_FIELD_SEP
    except ModuleNotFoundError as exc:
        if exc.name == "transformers":
            raise RuntimeError(
                "import failed because transformers is missing; install it with `python -m pip install transformers`"
            ) from exc
        raise RuntimeError(f"import failed because dependency {exc.name!r} is missing") from exc
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise RuntimeError(f"import failed: {exc}") from exc

    return {
        "np": np,
        "nano_graphrag": nano_graphrag,
        "GraphRAG": GraphRAG,
        "QueryParam": QueryParam,
        "chunking_by_seperators": chunking_by_seperators,
        "chunking_by_token_size": chunking_by_token_size,
        "get_chunks": get_chunks,
        "compute_mdhash_id": compute_mdhash_id,
        "wrap_embedding_func_with_attrs": wrap_embedding_func_with_attrs,
        "GRAPH_FIELD_SEP": GRAPH_FIELD_SEP,
    }


def _make_fake_hooks(core: dict[str, Any]):
    np = core["np"]
    wrap_embedding_func_with_attrs = core["wrap_embedding_func_with_attrs"]
    GRAPH_FIELD_SEP = core["GRAPH_FIELD_SEP"]
    compute_mdhash_id = core["compute_mdhash_id"]

    @wrap_embedding_func_with_attrs(embedding_dim=8, max_token_size=8192)
    async def fake_embedding(texts: list[str]):
        rows = []
        for text in texts:
            base = (sum(text.encode("utf-8")) % 97) + 1
            rows.append([(base + idx + 1) / 100.0 for idx in range(8)])
        return np.array(rows, dtype=np.float32)

    async def fake_model(prompt, system_prompt=None, history_messages=None, **kwargs) -> str:
        if kwargs.get("response_format") == {"type": "json_object"}:
            return json.dumps(
                {
                    "title": "Synthetic report",
                    "summary": "Synthetic community summary.",
                    "findings": [
                        {
                            "summary": "Synthetic finding",
                            "explanation": "The fake model produced deterministic JSON.",
                        }
                    ],
                    "points": [
                        {"description": "Synthetic support point for smoke testing.", "score": 1}
                    ],
                }
            )
        return "Synthetic answer."

    async def fake_entity_extraction(
        chunks,
        knwoledge_graph_inst,
        entity_vdb,
        tokenizer_wrapper,
        global_config,
        using_amazon_bedrock: bool = False,
    ):
        del tokenizer_wrapper, global_config, using_amazon_bedrock
        source_id = GRAPH_FIELD_SEP.join(chunks.keys())
        if not source_id:
            return None
        await knwoledge_graph_inst.upsert_node(
            "ALPHA",
            {
                "entity_type": "CONCEPT",
                "description": "Synthetic alpha entity for no-network smoke testing.",
                "source_id": source_id,
            },
        )
        await knwoledge_graph_inst.upsert_node(
            "BETA",
            {
                "entity_type": "CONCEPT",
                "description": "Synthetic beta entity for no-network smoke testing.",
                "source_id": source_id,
            },
        )
        await knwoledge_graph_inst.upsert_edge(
            "ALPHA",
            "BETA",
            {
                "weight": 1.0,
                "description": "Synthetic relationship between alpha and beta.",
                "source_id": source_id,
                "order": 1,
            },
        )
        if entity_vdb is not None:
            await entity_vdb.upsert(
                {
                    compute_mdhash_id("ALPHA", prefix="ent-"): {
                        "content": "ALPHA Synthetic alpha entity for no-network smoke testing.",
                        "entity_name": "ALPHA",
                    },
                    compute_mdhash_id("BETA", prefix="ent-"): {
                        "content": "BETA Synthetic beta entity for no-network smoke testing.",
                        "entity_name": "BETA",
                    },
                }
            )
        return knwoledge_graph_inst

    return fake_embedding, fake_model, fake_entity_extraction


def _build_rag(core: dict[str, Any], work_dir: Path):
    GraphRAG = core["GraphRAG"]
    fake_embedding, fake_model, fake_entity_extraction = _make_fake_hooks(core)
    return GraphRAG(
        working_dir=str(work_dir),
        enable_local=True,
        enable_naive_rag=True,
        embedding_func=fake_embedding,
        best_model_func=fake_model,
        cheap_model_func=fake_model,
        entity_extraction_func=fake_entity_extraction,
        chunk_token_size=64,
        chunk_overlap_token_size=8,
    )


def _check_chunking(core: dict[str, Any], rag: Any) -> None:
    get_chunks = core["get_chunks"]
    chunking_by_token_size = core["chunking_by_token_size"]
    chunking_by_seperators = core["chunking_by_seperators"]

    docs = {"doc-smoke": {"content": "Alpha beta gamma.\nBeta gamma delta."}}
    chunks = get_chunks(
        docs,
        chunk_func=chunking_by_token_size,
        tokenizer_wrapper=rag.tokenizer_wrapper,
        overlap_token_size=0,
        max_token_size=8,
    )
    if not chunks:
        raise AssertionError("get_chunks returned no chunks")
    for chunk in chunks.values():
        required = {"tokens", "content", "chunk_order_index", "full_doc_id"}
        if not required <= set(chunk):
            raise AssertionError(f"chunk missing required keys: {chunk}")
        if chunk["full_doc_id"] != "doc-smoke":
            raise AssertionError("chunk full_doc_id did not preserve doc key")

    tokens = [rag.tokenizer_wrapper.encode("Alpha.\nBeta.")]
    sep_chunks = chunking_by_seperators(
        tokens,
        ["doc-sep"],
        rag.tokenizer_wrapper,
        overlap_token_size=0,
        max_token_size=64,
    )
    if not sep_chunks or sep_chunks[0]["full_doc_id"] != "doc-sep":
        raise AssertionError("chunking_by_seperators did not produce expected schema")


def _check_query_guards(core: dict[str, Any], work_dir: Path) -> None:
    GraphRAG = core["GraphRAG"]
    QueryParam = core["QueryParam"]
    fake_embedding, fake_model, fake_entity_extraction = _make_fake_hooks(core)
    guard_rag = GraphRAG(
        working_dir=str(work_dir / "guard"),
        enable_local=False,
        enable_naive_rag=False,
        embedding_func=fake_embedding,
        best_model_func=fake_model,
        cheap_model_func=fake_model,
        entity_extraction_func=fake_entity_extraction,
    )

    try:
        guard_rag.query("local guard", param=QueryParam(mode="local"))
    except ValueError as exc:
        if "enable_local is False" not in str(exc):
            raise
    else:
        raise AssertionError("local query did not raise when enable_local=False")

    try:
        guard_rag.query("naive guard", param=QueryParam(mode="naive"))
    except ValueError as exc:
        if "enable_naive_rag is False" not in str(exc):
            raise
    else:
        raise AssertionError("naive query did not raise when enable_naive_rag=False")


def _check_insert_query_reload(core: dict[str, Any], work_dir: Path) -> None:
    QueryParam = core["QueryParam"]
    rag = _build_rag(core, work_dir / "main")
    rag.insert(
        [
            "Alpha works with Beta in a deterministic GraphRAG smoke document.",
            "Beta relates to Alpha and Gamma in a second deterministic smoke document.",
        ]
    )

    global_answer = rag.query("What is the synthetic relationship?", param=QueryParam(mode="global"))
    if global_answer != "Synthetic answer.":
        raise AssertionError(f"unexpected global answer: {global_answer!r}")

    local_context = rag.query(
        "Return local context about Alpha.",
        param=QueryParam(mode="local", only_need_context=True, top_k=2),
    )
    if not local_context or "-----Entities-----" not in local_context:
        raise AssertionError("local context-only query did not return entity context")

    naive_context = rag.query(
        "Return naive context about Alpha.",
        param=QueryParam(mode="naive", only_need_context=True, top_k=2),
    )
    if not naive_context or "Alpha" not in naive_context:
        raise AssertionError("naive context-only query did not return source chunk text")

    # Reconstruct from the same directory to prove default persistence/reload.
    rag_reloaded = _build_rag(core, work_dir / "main")
    reloaded_answer = rag_reloaded.query(
        "Can the reloaded graph answer?", param=QueryParam(mode="global")
    )
    if reloaded_answer != "Synthetic answer.":
        raise AssertionError(f"unexpected reloaded global answer: {reloaded_answer!r}")


def _run_with_dir(args: argparse.Namespace, work_dir: Path) -> int:
    try:
        core = _import_core()
        rag = _build_rag(core, work_dir / "construction")
        _check_chunking(core, rag)
        _check_query_guards(core, work_dir)
        if not args.skip_insert:
            _check_insert_query_reload(core, work_dir)
    except Exception as exc:
        return _fail(str(exc))

    version = getattr(core["nano_graphrag"], "__version__", "unknown")
    summary = {
        "status": "ok",
        "package_version": version,
        "work_dir": str(work_dir),
        "checks": [
            "import",
            "GraphRAG construction with fake hooks",
            "chunking schema",
            "local/naive query-mode guards",
        ]
        + ([] if args.skip_insert else ["insert", "global/local/naive query", "reload"]),
    }
    print(json.dumps(summary, indent=2))
    return 0


def main() -> int:
    args = _parse_args()
    if args.work_dir is not None:
        args.work_dir.mkdir(parents=True, exist_ok=True)
        return _run_with_dir(args, args.work_dir)

    if args.keep_work_dir:
        work_dir = Path(tempfile.mkdtemp(prefix="nano_graphrag_core_smoke_"))
        exit_code = _run_with_dir(args, work_dir)
        print(f"kept temporary work dir: {work_dir}")
        return exit_code

    with tempfile.TemporaryDirectory(prefix="nano_graphrag_core_smoke_") as temp_name:
        return _run_with_dir(args, Path(temp_name))


if __name__ == "__main__":
    raise SystemExit(main())
