#!/usr/bin/env python3
"""Inspect FlashRAG index_builder arguments without heavy imports.

This helper mirrors the public CLI shape of `python -m flashrag.retriever.index_builder`
well enough to validate commands, print an executable command, and explain likely
optional dependencies. It deliberately does not import FlashRAG, Faiss, torch, or
model libraries.
"""

from __future__ import annotations

import argparse
import importlib.util
import shlex
import sys
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect FlashRAG index_builder arguments safely.")
    parser.add_argument("--retrieval_method", type=str)
    parser.add_argument("--model_path", type=str, default=None)
    parser.add_argument("--corpus_path", type=str)
    parser.add_argument("--corpus_embedded_path", type=str, default=None)
    parser.add_argument("--save_dir", default="indexes/", type=str)
    parser.add_argument("--max_length", type=int, default=180)
    parser.add_argument("--batch_size", type=int, default=512)
    parser.add_argument("--use_fp16", default=False, action="store_true")
    parser.add_argument("--pooling_method", type=str, default=None)
    parser.add_argument("--instruction", type=str, default=None)
    parser.add_argument("--faiss_type", default=None, type=str)
    parser.add_argument("--embedding_path", default=None, type=str)
    parser.add_argument("--save_embedding", action="store_true", default=False)
    parser.add_argument("--faiss_gpu", default=False, action="store_true")
    parser.add_argument("--sentence_transformer", action="store_true", default=False)
    parser.add_argument("--bm25_backend", default="pyserini", choices=["bm25s", "pyserini"])
    parser.add_argument("--index_modal", type=str, default="all", choices=["text", "image", "all"])
    parser.add_argument("--n_postings", type=int, default=1000)
    parser.add_argument("--centroid_fraction", type=float, default=0.2)
    parser.add_argument("--min_cluster_size", type=int, default=2)
    parser.add_argument("--summary_energy", type=float, default=0.4)
    parser.add_argument("--nknn", type=int, default=0)
    parser.add_argument("--batched_indexing", type=int, default=10000)
    parser.add_argument(
        "--strict-paths",
        action="store_true",
        help="Fail when local corpus, model, embedding, or embedded-corpus paths are absent.",
    )
    parser.add_argument(
        "--check-imports",
        action="store_true",
        help="Check whether expected optional Python modules are importable without importing them.",
    )
    return parser.parse_args(argv)


def is_probably_local(path_text: str | None) -> bool:
    if not path_text:
        return False
    path = Path(path_text).expanduser()
    known_data_suffixes = {".jsonl", ".json", ".parquet", ".index", ".memmap", ".tsv", ".txt"}
    return path_text.startswith((".", "/", "~")) or path.exists() or path.suffix in known_data_suffixes


def command_for(args: argparse.Namespace) -> list[str]:
    command = ["python", "-m", "flashrag.retriever.index_builder"]
    defaults = parse_args([])
    option_names = [
        "retrieval_method",
        "model_path",
        "corpus_path",
        "corpus_embedded_path",
        "save_dir",
        "max_length",
        "batch_size",
        "pooling_method",
        "instruction",
        "faiss_type",
        "embedding_path",
        "bm25_backend",
        "index_modal",
        "n_postings",
        "centroid_fraction",
        "min_cluster_size",
        "summary_energy",
        "nknn",
        "batched_indexing",
    ]
    for name in option_names:
        value = getattr(args, name)
        default = getattr(defaults, name)
        if value is None:
            continue
        if name in {"retrieval_method", "corpus_path"} or value != default:
            command.extend([f"--{name}", str(value)])
    for name in ["use_fp16", "save_embedding", "faiss_gpu", "sentence_transformer"]:
        if getattr(args, name):
            command.append(f"--{name}")
    return command


def module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def add_path_check(messages: list[str], errors: list[str], label: str, value: str | None, strict: bool) -> None:
    if not value:
        return
    if is_probably_local(value):
        exists = Path(value).expanduser().exists()
        messages.append(f"{label}: {'found' if exists else 'not found'} ({value})")
        if strict and not exists:
            errors.append(f"{label} does not exist: {value}")
    else:
        messages.append(f"{label}: treated as model id or remote identifier ({value})")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    warnings: list[str] = []
    errors: list[str] = []
    notes: list[str] = []

    method = (args.retrieval_method or "").lower()
    if not method:
        errors.append("--retrieval_method is required")
    if not args.corpus_path and method != "serper":
        errors.append("--corpus_path is required for local index building")
    if args.max_length <= 0:
        errors.append("--max_length must be positive")
    if args.batch_size <= 0:
        errors.append("--batch_size must be positive")
    if args.n_postings <= 0:
        errors.append("--n_postings must be positive")
    if args.batched_indexing <= 0:
        errors.append("--batched_indexing must be positive")

    is_bm25 = method == "bm25"
    is_splade = method == "splade"
    is_clip = "clip" in method or (args.model_path is not None and "clip" in args.model_path.lower())
    is_dense = bool(method) and not is_bm25 and not is_splade and method != "serper"

    if is_bm25:
        if args.model_path:
            warnings.append("BM25 does not use --model_path; remove it unless this is a wrapper convention.")
        if args.bm25_backend == "bm25s":
            notes.append("BM25s backend: lightweight CPU-friendly option; requires bm25s and stemming support.")
        else:
            notes.append("Pyserini backend: requires pyserini and a compatible Java runtime.")
    elif is_splade:
        if not args.model_path:
            errors.append("SPLADE/Seismic indexing requires --model_path")
        notes.append("SPLADE uses Seismic sparse neural indexing and may need small batches.")
    elif is_dense:
        if not args.model_path:
            errors.append("Dense or CLIP indexing requires --model_path")
        if args.faiss_type is None:
            warnings.append("--faiss_type is omitted; FlashRAG defaults to Flat, but explicit Flat improves reproducibility.")
        if args.pooling_method is None and not args.sentence_transformer and not is_clip:
            warnings.append("--pooling_method is omitted; verify FlashRAG can infer the intended pooling method.")
        if args.sentence_transformer:
            notes.append("SentenceTransformers mode bypasses manual pooling but requires sentence-transformers.")
        if is_clip:
            notes.append("CLIP-style indexing may create text/image indexes depending on --index_modal.")
    elif method == "serper":
        warnings.append("Serper is a web retriever and is not built with index_builder.")

    add_path_check(notes, errors, "corpus_path", args.corpus_path, args.strict_paths)
    add_path_check(notes, errors, "model_path", args.model_path, args.strict_paths)
    add_path_check(notes, errors, "embedding_path", args.embedding_path, args.strict_paths)
    add_path_check(notes, errors, "corpus_embedded_path", args.corpus_embedded_path, args.strict_paths)

    expected_modules: list[str] = []
    if is_bm25 and args.bm25_backend == "bm25s":
        expected_modules.extend(["bm25s", "Stemmer"])
    if is_bm25 and args.bm25_backend == "pyserini":
        expected_modules.append("pyserini")
    if is_dense:
        expected_modules.extend(["faiss", "torch", "transformers"])
    if args.sentence_transformer:
        expected_modules.append("sentence_transformers")
    if is_splade:
        expected_modules.extend(["seismic", "torch", "transformers"])
    if is_clip:
        expected_modules.extend(["PIL", "requests"])

    if args.faiss_gpu:
        notes.append("--faiss_gpu requires GPU-capable Faiss; CPU-only Faiss is not enough.")

    if args.check_imports:
        for module_name in sorted(set(expected_modules)):
            if module_available(module_name):
                notes.append(f"module available: {module_name}")
            else:
                warnings.append(f"module not importable: {module_name}")
    elif expected_modules:
        notes.append("expected optional modules: " + ", ".join(sorted(set(expected_modules))))

    print("FlashRAG index_builder argument inspection")
    print("command:")
    print("  " + " ".join(shlex.quote(part) for part in command_for(args)))
    print("classification:")
    print(f"  method: {method or '<missing>'}")
    print(f"  family: {'bm25' if is_bm25 else 'splade/seismic' if is_splade else 'clip/multimodal' if is_clip else 'dense/faiss' if is_dense else 'web/none'}")
    print(f"  save_dir: {args.save_dir}")

    for note in notes:
        print(f"NOTE: {note}")
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors:
        print("status: failed")
        return 1
    print("status: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
