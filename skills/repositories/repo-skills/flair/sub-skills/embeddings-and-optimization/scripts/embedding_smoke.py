#!/usr/bin/env python3
"""
Safe no-download smoke checks for Flair embedding APIs.

Default behavior uses only in-memory dictionaries and tiny trainable embeddings.
It does not instantiate named pretrained models, download resources, train real
models, write files, or depend on a repository checkout.

Examples:
    python scripts/embedding_smoke.py --json
    python scripts/embedding_smoke.py --include-transformer --transformer-model distilbert-base-uncased --allow-downloads --json
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from typing import Any


def _set_environment(args: argparse.Namespace) -> None:
    # Flair chooses its device at import time, so set this before importing flair.
    os.environ.setdefault("FLAIR_DEVICE", args.device)
    if args.cache_root:
        os.environ.setdefault("FLAIR_CACHE_ROOT", args.cache_root)


def _import_flair() -> dict[str, Any]:
    try:
        import flair
        from flair.data import Dictionary, Sentence
        from flair.embeddings import (
            DocumentCNNEmbeddings,
            DocumentPoolEmbeddings,
            DocumentRNNEmbeddings,
            OneHotEmbeddings,
            StackedEmbeddings,
            TransformerDocumentEmbeddings,
            TransformerWordEmbeddings,
        )
    except Exception as exc:  # pragma: no cover - intentionally user-facing
        raise SystemExit(f"Could not import required Flair embedding APIs: {exc}") from exc

    return {
        "flair": flair,
        "Dictionary": Dictionary,
        "Sentence": Sentence,
        "DocumentCNNEmbeddings": DocumentCNNEmbeddings,
        "DocumentPoolEmbeddings": DocumentPoolEmbeddings,
        "DocumentRNNEmbeddings": DocumentRNNEmbeddings,
        "OneHotEmbeddings": OneHotEmbeddings,
        "StackedEmbeddings": StackedEmbeddings,
        "TransformerDocumentEmbeddings": TransformerDocumentEmbeddings,
        "TransformerWordEmbeddings": TransformerWordEmbeddings,
    }


def _build_vocab(Dictionary: Any) -> Any:
    vocab = Dictionary(add_unk=True)
    for item in ["Berlin", "loves", "Flair", ".", "tiny", "document", "works"]:
        vocab.add_item(item)
    return vocab


def _assert_token_width(sentence: Any, embeddings: Any) -> list[int]:
    names = embeddings.get_names()
    widths = [len(token.get_embedding(names)) for token in sentence]
    assert widths, "expected at least one token"
    assert all(width == embeddings.embedding_length for width in widths), (widths, embeddings.embedding_length)
    return widths


def _assert_document_width(sentence: Any, embeddings: Any) -> int:
    names = embeddings.get_names()
    width = len(sentence.get_embedding(names))
    assert width == embeddings.embedding_length, (width, embeddings.embedding_length)
    return width


def run_default_smoke(api: dict[str, Any]) -> dict[str, Any]:
    Dictionary = api["Dictionary"]
    Sentence = api["Sentence"]
    OneHotEmbeddings = api["OneHotEmbeddings"]
    StackedEmbeddings = api["StackedEmbeddings"]
    DocumentPoolEmbeddings = api["DocumentPoolEmbeddings"]
    DocumentRNNEmbeddings = api["DocumentRNNEmbeddings"]
    DocumentCNNEmbeddings = api["DocumentCNNEmbeddings"]

    vocab = _build_vocab(Dictionary)
    sentence = Sentence("Berlin loves Flair .")

    one_hot = OneHotEmbeddings(vocab_dictionary=vocab, embedding_length=8, stable=True)
    one_hot.embed(sentence)
    one_hot_widths = _assert_token_width(sentence, one_hot)
    assert len(sentence.get_embedding()) == 0, "token embedding should not create a sentence-level vector"

    sentence.clear_embeddings()
    assert all(len(token.get_embedding(one_hot.get_names())) == 0 for token in sentence)

    stacked = StackedEmbeddings(
        [
            OneHotEmbeddings(vocab_dictionary=vocab, embedding_length=8),
            OneHotEmbeddings(vocab_dictionary=vocab, embedding_length=4),
        ]
    )
    stacked.embed(sentence)
    stacked_widths = _assert_token_width(sentence, stacked)
    assert stacked.embedding_length == 12

    sentence.clear_embeddings()
    pooled = DocumentPoolEmbeddings([one_hot], pooling="mean", fine_tune_mode="none")
    pooled.embed(sentence)
    pooled_width = _assert_document_width(sentence, pooled)

    sentence.clear_embeddings()
    rnn = DocumentRNNEmbeddings([one_hot], hidden_size=5, bidirectional=False, dropout=0.0, rnn_type="GRU")
    rnn.embed(sentence)
    rnn_width = _assert_document_width(sentence, rnn)
    assert rnn_width == 5

    sentence.clear_embeddings()
    cnn = DocumentCNNEmbeddings([one_hot], kernels=((4, 2), (4, 3)), dropout=0.0, word_dropout=0.0, locked_dropout=0.0)
    cnn.embed(sentence)
    cnn_width = _assert_document_width(sentence, cnn)
    assert cnn_width == 8

    sentence.clear_embeddings()
    assert len(sentence.get_embedding()) == 0
    assert all(len(token.get_embedding()) == 0 for token in sentence)

    return {
        "one_hot_token_widths": one_hot_widths,
        "stacked_token_widths": stacked_widths,
        "stacked_embedding_length": stacked.embedding_length,
        "document_pool_width": pooled_width,
        "document_rnn_width": rnn_width,
        "document_cnn_width": cnn_width,
        "clear_embeddings_verified": True,
    }


def run_transformer_smoke(api: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    Sentence = api["Sentence"]
    TransformerWordEmbeddings = api["TransformerWordEmbeddings"]
    TransformerDocumentEmbeddings = api["TransformerDocumentEmbeddings"]

    local_only_kwargs: dict[str, Any] = {} if args.allow_downloads else {"local_files_only": True}
    common_kwargs = {
        "model": args.transformer_model,
        "layers": "-1",
        "fine_tune": False,
        # Pass local_files_only as a top-level transformers kwarg so tokenizer,
        # config, model, and feature-extractor resolution all honor the no-download
        # default used by the optional transformer smoke.
        **local_only_kwargs,
    }

    token_sentence = Sentence("Berlin loves transformer embeddings .")
    token_embeddings = TransformerWordEmbeddings(allow_long_sentences=False, layer_mean=True, **common_kwargs)
    token_embeddings.embed(token_sentence)
    token_widths = _assert_token_width(token_sentence, token_embeddings)
    token_sentence.clear_embeddings()

    doc_sentence = Sentence("A tiny document works .")
    doc_embeddings = TransformerDocumentEmbeddings(layer_mean=False, cls_pooling="cls", **common_kwargs)
    doc_embeddings.embed(doc_sentence)
    doc_width = _assert_document_width(doc_sentence, doc_embeddings)
    doc_sentence.clear_embeddings()

    return {
        "transformer_model": args.transformer_model,
        "allow_downloads": args.allow_downloads,
        "token_embedding_length": token_embeddings.embedding_length,
        "token_widths": token_widths,
        "document_embedding_length": doc_embeddings.embedding_length,
        "document_width": doc_width,
    }


def run_smoke(args: argparse.Namespace) -> dict[str, Any]:
    _set_environment(args)
    api = _import_flair()
    flair = api["flair"]
    if not args.verbose:
        logging.getLogger("flair").setLevel(logging.WARNING)
        if hasattr(flair, "logger"):
            flair.logger.setLevel(logging.WARNING)

    summary: dict[str, Any] = {
        "status": "ok",
        "flair_version": getattr(flair, "__version__", "unknown"),
        "device": str(getattr(flair, "device", "unknown")),
        "cache_root": str(getattr(flair, "cache_root", "unknown")),
        "downloads_attempted_by_default": False,
        "default_checks": run_default_smoke(api),
    }

    if args.include_transformer:
        summary["transformer_checks"] = run_transformer_smoke(api, args)
    else:
        summary["transformer_checks"] = "skipped; pass --include-transformer to opt in"

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe Flair embedding smoke checks.")
    parser.add_argument("--json", action="store_true", help="Print a JSON summary.")
    parser.add_argument("--verbose", action="store_true", help="Keep Flair INFO logging enabled during the smoke.")
    parser.add_argument("--device", default="cpu", help="Default FLAIR_DEVICE to set before importing Flair.")
    parser.add_argument("--cache-root", default=None, help="Optional FLAIR_CACHE_ROOT to set before importing Flair.")
    parser.add_argument(
        "--include-transformer",
        action="store_true",
        help="Also instantiate TransformerWordEmbeddings and TransformerDocumentEmbeddings.",
    )
    parser.add_argument(
        "--transformer-model",
        default="distilbert-base-uncased",
        help="Transformer model id or local path for the optional transformer check.",
    )
    parser.add_argument(
        "--allow-downloads",
        action="store_true",
        help="Allow optional transformer checks to resolve remote model files. Without this flag, local_files_only=True is passed.",
    )
    args = parser.parse_args()

    summary = run_smoke(args)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("Flair embedding smoke test passed")
        print(f"version={summary['flair_version']} device={summary['device']}")
        print(f"default_checks={summary['default_checks']}")
        print(f"transformer_checks={summary['transformer_checks']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
