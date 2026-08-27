#!/usr/bin/env python3
"""Smoke-check FlagEmbedding inference imports, signatures, and optional loads.

Default behavior is import/signature probing only. Model loading and encoding
are performed only when --model-name is explicitly supplied.
"""

from __future__ import annotations

import argparse
import inspect
import sys
from pathlib import Path
from typing import Any, Iterable, Optional


PUBLIC_SYMBOLS = [
    "FlagAutoModel",
    "FlagAutoReranker",
    "FlagModel",
    "BGEM3FlagModel",
    "FlagLLMModel",
    "FlagICLModel",
    "FlagPseudoMoEModel",
    "FlagReranker",
    "FlagLLMReranker",
    "LayerWiseFlagLLMReranker",
    "LightWeightFlagLLMReranker",
]

EMBEDDER_CLASS_IDS = [
    "encoder-only-base",
    "encoder-only-m3",
    "decoder-only-base",
    "decoder-only-icl",
    "decoder-only-pseudo_moe",
]

RERANKER_CLASS_IDS = [
    "encoder-only-base",
    "decoder-only-base",
    "decoder-only-layerwise",
    "decoder-only-lightweight",
]


def _parse_devices(value: Optional[str]) -> Any:
    if value is None or value == "auto":
        return None
    if "," in value:
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


def _parse_int_list(value: Optional[str]) -> Optional[list[int]]:
    if value is None or value == "":
        return None
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def _shape(value: Any) -> str:
    if value is None:
        return "None"
    if hasattr(value, "shape"):
        return str(tuple(value.shape))
    if isinstance(value, list):
        if not value:
            return "list[0]"
        return f"list[{len(value)}] first={_shape(value[0])}"
    if isinstance(value, dict):
        return "dict{" + ", ".join(f"{k}: {_shape(v)}" for k, v in value.items()) + "}"
    return type(value).__name__


def _print_signature(label: str, obj: Any) -> None:
    print(f"{label}: {inspect.signature(obj)}")


def _try_import_flagembedding() -> dict[str, Any]:
    import FlagEmbedding as flag_embedding
    from FlagEmbedding.abc.inference import AbsEmbedder, AbsReranker

    namespace = {name: getattr(flag_embedding, name) for name in PUBLIC_SYMBOLS}
    namespace["AbsEmbedder"] = AbsEmbedder
    namespace["AbsReranker"] = AbsReranker
    return namespace


def _import_flagembedding() -> dict[str, Any]:
    try:
        return _try_import_flagembedding()
    except ModuleNotFoundError as exc:
        if exc.name == "FlagEmbedding" and (Path.cwd() / "FlagEmbedding" / "__init__.py").exists():
            cwd = str(Path.cwd())
            if cwd not in sys.path:
                sys.path.insert(0, cwd)
            try:
                return _try_import_flagembedding()
            except ModuleNotFoundError as retry_exc:
                exc = retry_exc
            except Exception as retry_exc:  # pragma: no cover - depends on local package state
                raise RuntimeError(
                    f"Cannot import FlagEmbedding inference: {type(retry_exc).__name__}: {retry_exc}"
                ) from retry_exc
        missing = exc.name or str(exc)
        raise RuntimeError(
            f"Cannot import FlagEmbedding inference because required module {missing!r} is missing. "
            "Install package/runtime dependencies, then rerun this smoke probe."
        ) from exc
    except Exception as exc:  # pragma: no cover - depends on local package state
        raise RuntimeError(f"Cannot import FlagEmbedding inference: {type(exc).__name__}: {exc}") from exc


def probe_signatures(namespace: dict[str, Any]) -> None:
    print("FlagEmbedding inference import: ok")
    print("Public symbols:", ", ".join(PUBLIC_SYMBOLS))
    print("Embedder model_class ids:", ", ".join(EMBEDDER_CLASS_IDS))
    print("Reranker model_class ids:", ", ".join(RERANKER_CLASS_IDS))
    _print_signature("FlagAutoModel.from_finetuned", namespace["FlagAutoModel"].from_finetuned)
    _print_signature("FlagAutoReranker.from_finetuned", namespace["FlagAutoReranker"].from_finetuned)
    _print_signature("AbsEmbedder.encode_queries", namespace["AbsEmbedder"].encode_queries)
    _print_signature("AbsEmbedder.encode_corpus", namespace["AbsEmbedder"].encode_corpus)
    _print_signature("AbsReranker.compute_score", namespace["AbsReranker"].compute_score)
    _print_signature("BGEM3FlagModel.compute_score", namespace["BGEM3FlagModel"].compute_score)


def _load_embedder(args: argparse.Namespace, namespace: dict[str, Any]) -> Any:
    kwargs = {
        "model_class": args.model_class,
        "normalize_embeddings": not args.no_normalize_embeddings,
        "use_fp16": args.use_fp16,
        "use_bf16": args.use_bf16,
        "query_instruction_for_retrieval": args.query_instruction,
        "devices": _parse_devices(args.devices),
        "pooling_method": args.pooling_method,
        "trust_remote_code": args.trust_remote_code,
        "query_instruction_format": args.query_instruction_format,
        "truncate_dim": args.truncate_dim,
        "batch_size": args.batch_size,
        "query_max_length": args.query_max_length,
        "passage_max_length": args.passage_max_length,
    }
    if args.cache_dir:
        kwargs["cache_dir"] = args.cache_dir
    if args.domain_for_pseudo_moe:
        kwargs["domain_for_pseudo_moe"] = args.domain_for_pseudo_moe
    return namespace["FlagAutoModel"].from_finetuned(args.model_name, **kwargs)


def _load_reranker(args: argparse.Namespace, namespace: dict[str, Any]) -> Any:
    kwargs = {
        "model_class": args.model_class,
        "use_fp16": args.use_fp16,
        "trust_remote_code": args.trust_remote_code,
        "devices": _parse_devices(args.devices),
        "batch_size": args.batch_size,
        "query_max_length": args.query_max_length,
        "max_length": args.max_length,
        "normalize": args.normalize_scores,
    }
    if args.use_bf16:
        kwargs["use_bf16"] = True
    if args.cache_dir:
        kwargs["cache_dir"] = args.cache_dir
    cutoff_layers = _parse_int_list(args.cutoff_layers)
    compress_layers = _parse_int_list(args.compress_layers)
    if cutoff_layers is not None:
        kwargs["cutoff_layers"] = cutoff_layers
    if args.compress_ratio is not None:
        kwargs["compress_ratio"] = args.compress_ratio
    if compress_layers is not None:
        kwargs["compress_layers"] = compress_layers
    return namespace["FlagAutoReranker"].from_finetuned(args.model_name, **kwargs)


def _sanitize_mapping_error(exc: Exception, model_kind: str) -> str:
    text = str(exc)
    if "not found in the model mapping" in text:
        ids = EMBEDDER_CLASS_IDS if model_kind in {"embedder", "m3"} else RERANKER_CLASS_IDS
        return (
            "Auto mapping did not recognize this checkpoint. Re-run with --model-class set to one of: "
            + ", ".join(ids)
        )
    return f"{type(exc).__name__}: {text}"


def _first(items: Iterable[str], fallback: str) -> str:
    for item in items:
        if item:
            return item
    return fallback


def run_model_smoke(args: argparse.Namespace, namespace: dict[str, Any]) -> None:
    query = _first([args.query], "what is vector search?")
    passage = _first([args.passage], "Vector search compares embeddings for semantic retrieval.")

    if args.model_kind in {"embedder", "m3"}:
        model = _load_embedder(args, namespace)
        if args.model_kind == "m3":
            q = model.encode_queries(
                [query],
                batch_size=args.batch_size,
                return_dense=True,
                return_sparse=args.m3_return_sparse,
                return_colbert_vecs=args.m3_return_colbert_vecs,
            )
            p = model.encode_corpus(
                [passage],
                batch_size=args.batch_size,
                return_dense=True,
                return_sparse=args.m3_return_sparse,
                return_colbert_vecs=args.m3_return_colbert_vecs,
            )
            print("M3 query output:", _shape(q))
            print("M3 corpus output:", _shape(p))
            if q.get("dense_vecs") is not None and p.get("dense_vecs") is not None:
                dense_score = q["dense_vecs"] @ p["dense_vecs"].T
                print("M3 dense score shape:", _shape(dense_score))
            if args.m3_compute_score:
                scores = model.compute_score(
                    [(query, passage)],
                    batch_size=args.batch_size,
                    max_query_length=args.query_max_length,
                    max_passage_length=args.passage_max_length,
                )
                print("M3 compute_score output:", _shape(scores))
        else:
            q = model.encode_queries([query], batch_size=args.batch_size)
            p = model.encode_corpus([passage], batch_size=args.batch_size)
            print("Embedder query output:", _shape(q))
            print("Embedder corpus output:", _shape(p))
            try:
                score = q @ p.T
                print("Similarity shape:", _shape(score))
            except Exception as exc:
                print(f"Similarity check skipped: {type(exc).__name__}: {exc}")
    elif args.model_kind == "reranker":
        model = _load_reranker(args, namespace)
        score_kwargs: dict[str, Any] = {
            "batch_size": args.batch_size,
            "query_max_length": args.query_max_length,
            "max_length": args.max_length,
            "normalize": args.normalize_scores,
        }
        cutoff_layers = _parse_int_list(args.cutoff_layers)
        compress_layers = _parse_int_list(args.compress_layers)
        if cutoff_layers is not None:
            score_kwargs["cutoff_layers"] = cutoff_layers
        if args.compress_ratio is not None:
            score_kwargs["compress_ratio"] = args.compress_ratio
        if compress_layers is not None:
            score_kwargs["compress_layers"] = compress_layers
        scores = model.compute_score([(query, passage)], **score_kwargs)
        print("Reranker score output:", _shape(scores))
        print("Reranker scores:", scores)
    else:  # pragma: no cover - argparse enforces choices
        raise ValueError(f"Unsupported --model-kind {args.model_kind!r}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safe FlagEmbedding inference smoke probe. Defaults to import/signature checks only.",
    )
    parser.add_argument("--model-name", help="Optional local path or model id. Loading happens only when this is set.")
    parser.add_argument(
        "--model-kind",
        choices=["embedder", "m3", "reranker"],
        default="embedder",
        help="Which inference surface to smoke-check when --model-name is supplied.",
    )
    parser.add_argument("--model-class", help="Explicit FlagEmbedding model_class id for custom or unmapped checkpoints.")
    parser.add_argument("--devices", default="cpu", help="Device string, comma list, or 'auto'. Default: cpu.")
    parser.add_argument("--cache-dir", help="Optional model cache directory passed to from_pretrained.")
    parser.add_argument("--trust-remote-code", action="store_true", help="Allow custom model code for checkpoints that require it.")
    parser.add_argument("--use-fp16", action="store_true", help="Use fp16. Off by default for safe CPU smoke checks.")
    parser.add_argument("--use-bf16", action="store_true", help="Use bf16 where the concrete class supports it.")
    parser.add_argument("--no-normalize-embeddings", action="store_true", help="Disable dense embedding normalization for embedders.")
    parser.add_argument("--normalize-scores", action="store_true", help="Apply sigmoid normalization for reranker scores.")
    parser.add_argument("--pooling-method", help="Embedder pooling method such as cls, mean, or last_token.")
    parser.add_argument("--query-instruction", help="Query instruction for retrieval embedders.")
    parser.add_argument("--query-instruction-format", help="Instruction template with two placeholders.")
    parser.add_argument("--truncate-dim", type=int, help="Optional embedding dimension truncation.")
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size for the optional load/encode smoke. Default: 1.")
    parser.add_argument("--query-max-length", type=int, default=64, help="Query max length for the optional smoke. Default: 64.")
    parser.add_argument("--passage-max-length", type=int, default=128, help="Embedder passage max length. Default: 128.")
    parser.add_argument("--max-length", type=int, default=128, help="Reranker max length. Default: 128.")
    parser.add_argument("--cutoff-layers", help="Comma-separated layerwise/lightweight cutoff layers, for example 28 or 16,28.")
    parser.add_argument("--compress-ratio", type=int, choices=[1, 2, 4, 8], help="Lightweight reranker compression ratio.")
    parser.add_argument("--compress-layers", help="Comma-separated lightweight compression layers, for example 24,40.")
    parser.add_argument("--domain-for-pseudo-moe", help="Optional pseudo-MoE domain such as general, coding, or reasoning.")
    parser.add_argument("--m3-return-sparse", action="store_true", help="Return M3 sparse lexical weights during optional M3 smoke.")
    parser.add_argument("--m3-return-colbert-vecs", action="store_true", help="Return M3 ColBERT vectors during optional M3 smoke.")
    parser.add_argument("--m3-compute-score", action="store_true", help="Also call BGEM3FlagModel.compute_score during optional M3 smoke.")
    parser.add_argument("--query", default="what is vector search?", help="Toy query text for optional model smoke.")
    parser.add_argument("--passage", default="Vector search compares embeddings for semantic retrieval.", help="Toy passage text for optional model smoke.")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        namespace = _import_flagembedding()
        probe_signatures(namespace)
        if args.model_name:
            print("Model load smoke: enabled by --model-name")
            run_model_smoke(args, namespace)
        else:
            print("Model load smoke: skipped because --model-name was not supplied")
        return 0
    except Exception as exc:
        message = _sanitize_mapping_error(exc, args.model_kind)
        print(f"ERROR: {message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
