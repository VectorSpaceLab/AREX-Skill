#!/usr/bin/env python3
"""Safe LightRAG document-pipeline symbol and option sanity check.

This script imports installed LightRAG modules and validates public parser,
chunker, and pipeline symbols without starting services, initializing storages,
calling models, touching parser artifacts, or running repository tests.
"""

from __future__ import annotations

import inspect
import json
import sys
from typing import Any


def _fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def _require_attrs(module: Any, names: list[str]) -> None:
    missing = [name for name in names if not hasattr(module, name)]
    if missing:
        _fail(f"{module.__name__} missing symbols: {', '.join(missing)}")


def main() -> None:
    try:
        import lightrag.chunker as chunker
        import lightrag.parser.routing as routing
        from lightrag.pipeline import _PipelineMixin
    except Exception as exc:  # pragma: no cover - diagnostic script
        _fail(f"import failed: {exc!r}")

    routing_symbols = [
        "resolve_file_parser_engine",
        "resolve_parser_directives",
        "resolve_file_parser_directives",
        "parse_process_options",
        "validate_process_options",
        "encode_parse_engine",
        "decode_parse_engine",
        "resolve_chunk_options",
        "slim_chunk_options",
        "chunk_strategy_key",
        "default_chunker_config",
    ]
    chunker_symbols = [
        "chunking_by_fixed_token",
        "chunking_by_recursive_character",
        "chunking_by_semantic_vector",
        "chunking_by_paragraph_semantic",
        "chunking_by_token_size",
    ]
    pipeline_symbols = [
        "apipeline_enqueue_documents",
        "apipeline_process_enqueue_documents",
        "analyze_multimodal",
        "_build_mm_chunks_from_sidecars",
    ]

    _require_attrs(routing, routing_symbols)
    _require_attrs(chunker, chunker_symbols)
    missing_pipeline = [name for name in pipeline_symbols if not hasattr(_PipelineMixin, name)]
    if missing_pipeline:
        _fail(f"_PipelineMixin missing methods: {', '.join(missing_pipeline)}")

    enqueue_sig = inspect.signature(_PipelineMixin.apipeline_enqueue_documents)
    for parameter in ["parse_engine", "process_options", "chunk_options", "from_scan"]:
        if parameter not in enqueue_sig.parameters:
            _fail(f"apipeline_enqueue_documents missing parameter {parameter!r}")

    process_opts = routing.parse_process_options("iteP!")
    if not (
        process_opts.images
        and process_opts.tables
        and process_opts.equations
        and process_opts.skip_kg
        and process_opts.chunking == "P"
        and process_opts.chunking_explicit
    ):
        _fail("parse_process_options did not decode 'iteP!' as expected")

    errors = routing.validate_process_options("RV")
    if not errors:
        _fail("validate_process_options did not reject multiple chunk selectors")

    encoded = routing.encode_parse_engine(
        "mineru", {"page_range": ["1-3"], "language": "en"}
    )
    engine, params, decode_errors = routing.decode_parse_engine(encoded)
    if decode_errors or engine != "mineru" or params.get("language") != "en":
        _fail(f"engine parameter round trip failed: {encoded!r} -> {params!r} / {decode_errors!r}")

    directives = routing.resolve_parser_directives(
        "sample.[native-teP(chunk_ts=2100)].docx",
        parser_rules="*:legacy-R",
        require_external_endpoint=False,
    )
    if directives.engine != "native" or directives.process_options != "teP":
        _fail(f"unexpected parser directives: {directives!r}")
    if directives.chunk_params.get("P", {}).get("chunk_token_size") != 2100:
        _fail(f"P chunk params not decoded: {directives.chunk_params!r}")

    fixed_options = routing.resolve_chunk_options({}, process_options="F")
    paragraph_options = routing.resolve_chunk_options({}, process_options="P")
    if "fixed_token" not in fixed_options:
        _fail(f"fixed chunk options missing fixed_token: {fixed_options!r}")
    if "paragraph_semantic" not in paragraph_options:
        _fail(f"P chunk options missing paragraph_semantic: {paragraph_options!r}")

    result = {
        "ok": True,
        "routing_symbols": routing_symbols,
        "chunker_symbols": chunker_symbols,
        "pipeline_methods": pipeline_symbols,
        "enqueue_signature": str(enqueue_sig),
        "sample_directives": {
            "engine": directives.engine,
            "process_options": directives.process_options,
            "chunk_params": directives.chunk_params,
            "engine_params": directives.engine_params,
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
