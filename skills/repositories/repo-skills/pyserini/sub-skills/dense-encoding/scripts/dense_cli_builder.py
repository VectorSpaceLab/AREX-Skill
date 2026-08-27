#!/usr/bin/env python3
"""Build safe Pyserini dense encoding/search command templates without importing Pyserini."""

from __future__ import annotations

import argparse
import shlex
from typing import Iterable


ENCODE_CLASSES = [
    "dpr",
    "bpr",
    "tct_colbert",
    "ance",
    "sentence-transformers",
    "openai-api",
    "auto",
    "contriever",
    "arctic",
    "splade",
    "uniir",
    "qwen3",
    "dse",
    "mmeb",
]

FAISS_QUERY_CLASSES = [
    "dkrr",
    "dpr",
    "bpr",
    "tct_colbert",
    "ance",
    "sentence",
    "contriever",
    "auto",
    "aggretriever",
    "openai-api",
    "cosdpr",
    "arctic",
    "uniir",
    "qwen3",
    "dse",
    "mmeb",
]


def extend_option(command: list[str], option: str, values: list[str] | None) -> None:
    if values:
        command.append(option)
        command.extend(values)


def add_option(command: list[str], option: str, value) -> None:
    if value is not None:
        command.extend([option, str(value)])


def add_flag(command: list[str], option: str, enabled: bool) -> None:
    if enabled:
        command.append(option)


def print_command(command: list[str]) -> None:
    print(" ".join(shlex.quote(part) for part in command))


def encode_command(args: argparse.Namespace) -> list[str]:
    command = ["python", "-m", "pyserini.encode"]
    command.append("input")
    add_option(command, "--corpus", args.corpus)
    extend_option(command, "--fields", args.fields)
    add_option(command, "--docid-field", args.docid_field)
    add_option(command, "--delimiter", args.delimiter)
    add_option(command, "--shard-id", args.shard_id)
    add_option(command, "--shard-num", args.shard_num)

    command.append("output")
    add_option(command, "--embeddings", args.embeddings)
    add_flag(command, "--to-faiss", args.to_faiss)

    command.append("encoder")
    add_option(command, "--encoder", args.encoder)
    add_option(command, "--encoder-class", args.encoder_class)
    extend_option(command, "--fields", args.encoder_fields or args.fields)
    add_flag(command, "--multimodal", args.multimodal)
    add_option(command, "--batch-size", args.batch_size)
    add_option(command, "--max-length", args.max_length)
    add_option(command, "--dimension", args.dimension)
    add_option(command, "--device", args.device)
    add_flag(command, "--fp16", args.fp16)
    add_flag(command, "--add-sep", args.add_sep)
    add_option(command, "--pooling", args.pooling)
    add_flag(command, "--l2-norm", args.l2_norm)
    add_option(command, "--prefix", args.prefix)
    add_flag(command, "--use-openai", args.use_openai)
    add_option(command, "--rate-limit", args.rate_limit)
    add_flag(command, "--explicit-truncate", args.explicit_truncate)
    return command


def faiss_index_command(args: argparse.Namespace) -> list[str]:
    command = ["python", "-m", "pyserini.index.faiss"]
    add_option(command, "--input", args.input)
    add_option(command, "--output", args.output)
    add_option(command, "--dim", args.dim)
    add_flag(command, "--hnsw", args.hnsw)
    add_option(command, "--M", args.M)
    add_option(command, "--efC", args.efC)
    add_flag(command, "--pq", args.pq)
    add_option(command, "--pq-m", args.pq_m)
    add_option(command, "--pq-nbits", args.pq_nbits)
    add_option(command, "--threads", args.threads)
    add_option(command, "--metric", args.metric)
    add_option(command, "--device", args.device)
    return command


def faiss_search_command(args: argparse.Namespace) -> list[str]:
    command = ["python", "-m", "pyserini.search.faiss"]
    add_option(command, "--index", args.index)
    add_option(command, "--topics", args.topics)
    add_option(command, "--output", args.output)
    add_option(command, "--hits", args.hits)
    add_option(command, "--binary-hits", args.binary_hits)
    add_flag(command, "--rerank", args.rerank)
    add_option(command, "--topics-format", args.topics_format)
    add_option(command, "--output-format", args.output_format)
    add_flag(command, "--max-passage", args.max_passage)
    add_option(command, "--max-passage-hits", args.max_passage_hits)
    add_option(command, "--max-passage-delimiter", args.max_passage_delimiter)
    add_option(command, "--batch-size", args.batch_size)
    add_option(command, "--threads", args.threads)
    add_flag(command, "--fp16", args.fp16)
    add_flag(command, "--remove-query", args.remove_query)
    add_flag(command, "--explicit-truncate", args.explicit_truncate)
    add_option(command, "--instruction-config", args.instruction_config)
    add_option(command, "--encoder-class", args.encoder_class)
    add_option(command, "--encoder", args.encoder)
    add_flag(command, "--multimodal", args.multimodal)
    add_option(command, "--pooling", args.pooling)
    add_flag(command, "--l2-norm", args.l2_norm)
    add_option(command, "--tokenizer", args.tokenizer)
    add_option(command, "--encoded-queries", args.encoded_queries)
    add_option(command, "--pca-model", args.pca_model)
    add_option(command, "--device", args.device)
    add_option(command, "--query-prefix", args.query_prefix)
    add_option(command, "--searcher", args.searcher)
    add_option(command, "--max-length", args.max_length)
    add_option(command, "--prf-depth", args.prf_depth)
    add_option(command, "--prf-method", args.prf_method)
    add_option(command, "--rocchio-alpha", args.rocchio_alpha)
    add_option(command, "--rocchio-beta", args.rocchio_beta)
    add_option(command, "--rocchio-gamma", args.rocchio_gamma)
    add_option(command, "--rocchio-topk", args.rocchio_topk)
    add_option(command, "--rocchio-bottomk", args.rocchio_bottomk)
    add_option(command, "--sparse-index", args.sparse_index)
    add_option(command, "--ance-prf-encoder", args.ance_prf_encoder)
    add_option(command, "--ef-search", args.ef_search)
    add_flag(command, "--normalize-distances", args.normalize_distances)
    add_option(command, "--faiss-device", args.faiss_device)
    return command


def lucene_dense_search_command(args: argparse.Namespace) -> list[str]:
    command = ["python", "-m", "pyserini.search.lucene"]
    add_option(command, "--index", args.index)
    add_option(command, "--topics", args.topics)
    add_option(command, "--output", args.output)
    add_flag(command, "--dense", True)
    add_flag(command, "--hnsw", args.hnsw)
    add_flag(command, "--flat", args.flat)
    add_option(command, "--ef-search", args.ef_search)
    add_option(command, "--onnx-encoder", args.onnx_encoder)
    add_option(command, "--hits", args.hits)
    add_option(command, "--topics-format", args.topics_format)
    add_option(command, "--output-format", args.output_format)
    add_option(command, "--batch-size", args.batch_size)
    add_option(command, "--threads", args.threads)
    add_flag(command, "--remove-query", args.remove_query)
    return command


def hybrid_search_command(args: argparse.Namespace) -> list[str]:
    command = ["python", "-m", "pyserini.search.hybrid"]
    command.append("dense")
    add_option(command, "--index", args.dense_index)
    add_option(command, "--encoder", args.encoder)
    add_option(command, "--encoder-class", args.encoder_class)
    add_option(command, "--encoded-queries", args.encoded_queries)
    add_option(command, "--device", args.device)
    add_option(command, "--faiss-device", args.faiss_device)
    add_option(command, "--pooling", args.pooling)
    add_flag(command, "--l2-norm", args.l2_norm)
    add_option(command, "--query-prefix", args.query_prefix)

    command.append("sparse")
    add_option(command, "--index", args.sparse_index)
    add_flag(command, "--impact", args.impact)
    add_option(command, "--encoder", args.sparse_encoder)
    add_option(command, "--onnx-encoder", args.sparse_onnx_encoder)
    add_option(command, "--k1", args.k1)
    add_option(command, "--b", args.b)
    add_option(command, "--language", args.language)

    command.append("fusion")
    add_option(command, "--alpha", args.alpha)
    add_option(command, "--hits", args.fusion_hits)
    add_flag(command, "--normalization", args.normalization)
    add_flag(command, "--weight-on-dense", args.weight_on_dense)

    command.append("run")
    add_option(command, "--topics", args.topics)
    add_option(command, "--output", args.output)
    add_option(command, "--hits", args.hits)
    add_option(command, "--topics-format", args.topics_format)
    add_option(command, "--output-format", args.output_format)
    add_option(command, "--batch-size", args.batch_size)
    add_option(command, "--threads", args.threads)
    return command


def add_common_search_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--topics", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--hits", type=int, default=1000)
    parser.add_argument("--topics-format", default=None)
    parser.add_argument("--output-format", default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--threads", type=int, default=None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Pyserini dense workflow commands without running them.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    encode = subparsers.add_parser("encode", help="Build a pyserini.encode corpus-encoding command.")
    encode.set_defaults(builder=encode_command)
    encode.add_argument("--corpus", required=True)
    encode.add_argument("--embeddings", required=True)
    encode.add_argument("--encoder", required=True)
    encode.add_argument("--fields", nargs="+", default=["text"])
    encode.add_argument("--encoder-fields", nargs="+")
    encode.add_argument("--docid-field")
    encode.add_argument("--delimiter", default="\\n")
    encode.add_argument("--shard-id", type=int)
    encode.add_argument("--shard-num", type=int)
    encode.add_argument("--to-faiss", action="store_true")
    encode.add_argument("--encoder-class", choices=ENCODE_CLASSES)
    encode.add_argument("--multimodal", action="store_true")
    encode.add_argument("--batch-size", type=int, default=64)
    encode.add_argument("--max-length", type=int, default=256)
    encode.add_argument("--dimension", type=int, default=768)
    encode.add_argument("--device", default="cpu")
    encode.add_argument("--fp16", action="store_true")
    encode.add_argument("--add-sep", action="store_true")
    encode.add_argument("--pooling", choices=["cls", "mean", "last", "eos"])
    encode.add_argument("--l2-norm", action="store_true")
    encode.add_argument("--prefix")
    encode.add_argument("--use-openai", action="store_true")
    encode.add_argument("--rate-limit", type=int)
    encode.add_argument("--explicit-truncate", action="store_true")

    index = subparsers.add_parser("faiss-index", help="Build a pyserini.index.faiss command.")
    index.set_defaults(builder=faiss_index_command)
    index.add_argument("--input", required=True)
    index.add_argument("--output", required=True)
    index.add_argument("--dim", type=int, default=768)
    index.add_argument("--hnsw", action="store_true")
    index.add_argument("--M", type=int)
    index.add_argument("--efC", type=int)
    index.add_argument("--pq", action="store_true")
    index.add_argument("--pq-m", type=int)
    index.add_argument("--pq-nbits", type=int)
    index.add_argument("--threads", type=int)
    index.add_argument("--metric", choices=["inner", "l2"])
    index.add_argument("--device", default="cpu")

    faiss = subparsers.add_parser("faiss-search", help="Build a pyserini.search.faiss command.")
    faiss.set_defaults(builder=faiss_search_command)
    faiss.add_argument("--index", required=True)
    add_common_search_args(faiss)
    faiss.add_argument("--binary-hits", type=int)
    faiss.add_argument("--rerank", action="store_true")
    faiss.add_argument("--max-passage", action="store_true")
    faiss.add_argument("--max-passage-hits", type=int)
    faiss.add_argument("--max-passage-delimiter")
    faiss.add_argument("--fp16", action="store_true")
    faiss.add_argument("--remove-query", action="store_true")
    faiss.add_argument("--explicit-truncate", action="store_true")
    faiss.add_argument("--instruction-config")
    faiss.add_argument("--encoder-class", choices=FAISS_QUERY_CLASSES)
    faiss.add_argument("--encoder")
    faiss.add_argument("--multimodal", action="store_true")
    faiss.add_argument("--pooling", choices=["cls", "mean", "last", "eos"])
    faiss.add_argument("--l2-norm", action="store_true")
    faiss.add_argument("--tokenizer")
    faiss.add_argument("--encoded-queries")
    faiss.add_argument("--pca-model")
    faiss.add_argument("--device", default="cpu")
    faiss.add_argument("--query-prefix")
    faiss.add_argument("--searcher")
    faiss.add_argument("--max-length", type=int)
    faiss.add_argument("--prf-depth", type=int)
    faiss.add_argument("--prf-method", choices=["avg", "rocchio", "ance-prf"])
    faiss.add_argument("--rocchio-alpha", type=float)
    faiss.add_argument("--rocchio-beta", type=float)
    faiss.add_argument("--rocchio-gamma", type=float)
    faiss.add_argument("--rocchio-topk", type=int)
    faiss.add_argument("--rocchio-bottomk", type=int)
    faiss.add_argument("--sparse-index")
    faiss.add_argument("--ance-prf-encoder")
    faiss.add_argument("--ef-search", type=int)
    faiss.add_argument("--normalize-distances", action="store_true")
    faiss.add_argument("--faiss-device", default="cpu")

    lucene = subparsers.add_parser("lucene-dense-search", help="Build a pyserini.search.lucene dense command.")
    lucene.set_defaults(builder=lucene_dense_search_command)
    lucene.add_argument("--index", required=True)
    add_common_search_args(lucene)
    lucene_index_type = lucene.add_mutually_exclusive_group(required=True)
    lucene_index_type.add_argument("--hnsw", action="store_true")
    lucene_index_type.add_argument("--flat", action="store_true")
    lucene.add_argument("--ef-search", type=int)
    lucene.add_argument("--onnx-encoder")
    lucene.add_argument("--remove-query", action="store_true")

    hybrid = subparsers.add_parser("hybrid-search", help="Build a pyserini.search.hybrid command.")
    hybrid.set_defaults(builder=hybrid_search_command)
    hybrid.add_argument("--dense-index", required=True)
    hybrid.add_argument("--sparse-index", required=True)
    add_common_search_args(hybrid)
    hybrid.add_argument("--encoder")
    hybrid.add_argument("--encoder-class", choices=FAISS_QUERY_CLASSES)
    hybrid.add_argument("--encoded-queries")
    hybrid.add_argument("--device", default="cpu")
    hybrid.add_argument("--faiss-device", default="cpu")
    hybrid.add_argument("--pooling", choices=["cls", "mean", "last", "eos"])
    hybrid.add_argument("--l2-norm", action="store_true")
    hybrid.add_argument("--query-prefix")
    hybrid.add_argument("--impact", action="store_true")
    hybrid.add_argument("--sparse-encoder")
    hybrid.add_argument("--sparse-onnx-encoder")
    hybrid.add_argument("--k1", type=float)
    hybrid.add_argument("--b", type=float)
    hybrid.add_argument("--language")
    hybrid.add_argument("--alpha", type=float, default=0.1)
    hybrid.add_argument("--fusion-hits", type=int, default=1000)
    hybrid.add_argument("--normalization", action="store_true")
    hybrid.add_argument("--weight-on-dense", action="store_true")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.builder(args)
    print_command(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
