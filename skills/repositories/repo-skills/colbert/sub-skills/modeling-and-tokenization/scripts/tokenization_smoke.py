#!/usr/bin/env python3
"""Smoke-test ColBERT query/document tokenization markers and shapes."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any


DEFAULT_QUERIES = [
    "what is contextual late interaction?",
    "how does colbert tokenize queries with mask padding?",
]

DEFAULT_DOCS = [
    "ColBERT encodes passages into token-level embedding matrices.",
    "The query and document marker tokens are inserted after the first special token.",
]


def _is_probably_local_checkpoint(value: str) -> bool:
    return value.endswith(".dnn") or os.path.exists(value)


def _shape(value: Any) -> str:
    return "x".join(str(part) for part in tuple(value.shape))


def _as_bool(value: Any) -> bool:
    if hasattr(value, "item"):
        return bool(value.item())
    return bool(value)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate ColBERT QueryTokenizer and DocTokenizer marker placement "
            "with a tiny fixture. Prefer local paths; remote names require --allow-remote."
        )
    )
    parser.add_argument(
        "--checkpoint",
        required=True,
        help="Local ColBERT checkpoint directory/.dnn file, or a Hugging Face name with --allow-remote.",
    )
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        help="Allow non-local Hugging Face model/repo names that may require network or cache access.",
    )
    parser.add_argument(
        "--query-maxlen",
        type=int,
        default=None,
        help="Optional query_maxlen override for diagnostics.",
    )
    parser.add_argument(
        "--doc-maxlen",
        type=int,
        default=None,
        help="Optional doc_maxlen override for diagnostics.",
    )
    parser.add_argument(
        "--query",
        action="append",
        dest="queries",
        help="Query text. May be repeated; defaults to a tiny built-in fixture.",
    )
    parser.add_argument(
        "--doc",
        action="append",
        dest="docs",
        help="Document text. May be repeated; defaults to a tiny built-in fixture.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print decoded token sequences.",
    )
    args = parser.parse_args()

    if not args.allow_remote and not _is_probably_local_checkpoint(args.checkpoint):
        print(
            "Refusing non-local checkpoint name without --allow-remote. "
            "Pass a local checkpoint path for offline-safe tokenization.",
            file=sys.stderr,
        )
        return 2

    queries = args.queries or DEFAULT_QUERIES
    docs = args.docs or DEFAULT_DOCS

    try:
        from colbert.infra import ColBERTConfig
        from colbert.modeling.tokenization import DocTokenizer, QueryTokenizer
    except Exception as exc:  # pragma: no cover - diagnostic script
        print(f"Failed to import ColBERT tokenization APIs: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    try:
        loaded_config = ColBERTConfig.load_from_checkpoint(args.checkpoint)
        base_config = loaded_config or ColBERTConfig(checkpoint=args.checkpoint)
        override_kwargs = {}
        if args.query_maxlen is not None:
            override_kwargs["query_maxlen"] = args.query_maxlen
        if args.doc_maxlen is not None:
            override_kwargs["doc_maxlen"] = args.doc_maxlen
        config = (
            ColBERTConfig.from_existing(base_config, ColBERTConfig(**override_kwargs))
            if override_kwargs
            else base_config
        )
        if config.checkpoint is None:
            config.set("checkpoint", args.checkpoint)

        query_tokenizer = QueryTokenizer(config, verbose=0)
        doc_tokenizer = DocTokenizer(config)
        q_ids, q_mask = query_tokenizer.tensorize(queries)
        d_ids, d_mask = doc_tokenizer.tensorize(docs)
    except Exception as exc:  # pragma: no cover - depends on local package/checkpoint
        print(f"Tokenization failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    checks = [
        ("query marker at column 1", _as_bool((q_ids[:, 1] == query_tokenizer.Q_marker_token_id).all())),
        ("document marker at column 1", _as_bool((d_ids[:, 1] == doc_tokenizer.D_marker_token_id).all())),
        ("query ids/mask shape match", tuple(q_ids.shape) == tuple(q_mask.shape)),
        ("document ids/mask shape match", tuple(d_ids.shape) == tuple(d_mask.shape)),
        ("query width equals config.query_maxlen", q_ids.shape[1] == config.query_maxlen),
        ("document width does not exceed config.doc_maxlen", d_ids.shape[1] <= config.doc_maxlen),
    ]

    print("ColBERT tokenization smoke summary")
    print(f"checkpoint: {args.checkpoint}")
    print(f"loaded metadata: {'yes' if loaded_config is not None else 'no'}")
    print(f"query_maxlen: {config.query_maxlen}")
    print(f"doc_maxlen: {config.doc_maxlen}")
    print(f"query ids shape: {_shape(q_ids)}")
    print(f"query mask shape: {_shape(q_mask)}")
    print(f"document ids shape: {_shape(d_ids)}")
    print(f"document mask shape: {_shape(d_mask)}")
    print(f"query marker id: {query_tokenizer.Q_marker_token_id}")
    print(f"document marker id: {doc_tokenizer.D_marker_token_id}")

    if args.verbose:
        print("decoded queries:")
        for decoded in query_tokenizer.tok.batch_decode(q_ids):
            print(decoded)
        print("decoded documents:")
        for decoded in doc_tokenizer.tok.batch_decode(d_ids):
            print(decoded)

    failed = False
    for label, ok in checks:
        print(f"{label}: {'ok' if ok else 'FAIL'}")
        failed = failed or not ok

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
