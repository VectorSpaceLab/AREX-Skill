#!/usr/bin/env python3
"""Search a text corpus with text2vec BM25 or dense cosine search.

BM25 mode uses lexical scoring and does not load neural models. Dense mode either
uses precomputed embeddings or, when --model-name is supplied, encodes texts with
SentenceModel and may need local/cached model weights.
"""

import argparse
import csv
import json
import math
import sys
from pathlib import Path


def die(message, code=2):
    print("error: {}".format(message), file=sys.stderr)
    raise SystemExit(code)


def infer_collection_format(path, requested):
    if requested != "auto":
        return requested
    suffix = path.suffix.lower()
    if suffix in (".jsonl", ".ndjson"):
        return "jsonl"
    if suffix == ".csv":
        return "csv"
    if suffix == ".tsv":
        return "tsv"
    return "text"


def infer_embedding_format(path, requested):
    if requested != "auto":
        return requested
    suffix = path.suffix.lower()
    if suffix == ".json":
        return "json"
    if suffix in (".jsonl", ".ndjson"):
        return "jsonl"
    if suffix == ".csv":
        return "csv"
    if suffix == ".tsv":
        return "tsv"
    return "json"


def read_jsonl_objects(path):
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                die("{}:{} is not valid JSON: {}".format(path, line_no, exc))
            rows.append(item)
    return rows


def read_delimited(path, delimiter):
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        if not reader.fieldnames:
            die("{} must have a header row".format(path))
        return [dict(row) for row in reader]


def read_texts(path, fmt, text_column):
    if not path.exists():
        die("text file does not exist: {}".format(path))
    texts = []
    if fmt == "text":
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                value = line.rstrip("\n")
                if value.strip():
                    texts.append(value)
    elif fmt == "jsonl":
        for idx, item in enumerate(read_jsonl_objects(path), 1):
            if not isinstance(item, dict):
                die("{} JSONL row {} must be an object for text loading".format(path, idx))
            value = str(item.get(text_column, "")).strip()
            if value:
                texts.append(value)
    elif fmt in ("csv", "tsv"):
        rows = read_delimited(path, "," if fmt == "csv" else "\t")
        for idx, row in enumerate(rows, 1):
            if text_column not in row:
                die("{} row {} missing text column {!r}".format(path, idx, text_column))
            value = str(row[text_column]).strip()
            if value:
                texts.append(value)
    else:
        die("unsupported text format: {}".format(fmt))
    if not texts:
        die("no non-empty text rows loaded from {}".format(path))
    return texts


def parse_vector(value, context):
    if isinstance(value, (list, tuple)):
        raw = list(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            die("empty vector in {}".format(context))
        if text.startswith("["):
            try:
                raw = json.loads(text)
            except json.JSONDecodeError as exc:
                die("bad JSON vector in {}: {}".format(context, exc))
        else:
            text = text.strip("()")
            pieces = text.split(",") if "," in text else text.split()
            raw = [p.strip() for p in pieces if p.strip()]
    else:
        die("unsupported vector value in {}".format(context))

    if not isinstance(raw, (list, tuple)):
        die("vector in {} must be a list of numbers".format(context))
    vector = []
    for idx, item in enumerate(raw):
        try:
            vector.append(float(item))
        except (TypeError, ValueError):
            die("vector item {} in {} is not numeric: {!r}".format(idx, context, item))
    if not vector:
        die("vector in {} is empty".format(context))
    return vector


def load_embeddings(path, fmt, vector_column):
    if not path.exists():
        die("embedding file does not exist: {}".format(path))
    vectors = []
    if fmt == "json":
        with path.open("r", encoding="utf-8") as handle:
            try:
                data = json.load(handle)
            except json.JSONDecodeError as exc:
                die("{} is not valid JSON: {}".format(path, exc))
        if isinstance(data, dict):
            if "embeddings" not in data:
                die("{} JSON object must contain an 'embeddings' list".format(path))
            data = data["embeddings"]
        if not isinstance(data, list):
            die("{} JSON embeddings must be a list".format(path))
        for idx, item in enumerate(data):
            value = item.get(vector_column) if isinstance(item, dict) else item
            vectors.append(parse_vector(value, "{} item {}".format(path, idx)))
    elif fmt == "jsonl":
        for idx, item in enumerate(read_jsonl_objects(path), 1):
            value = item.get(vector_column) if isinstance(item, dict) else item
            vectors.append(parse_vector(value, "{} row {}".format(path, idx)))
    elif fmt in ("csv", "tsv"):
        rows = read_delimited(path, "," if fmt == "csv" else "\t")
        for idx, row in enumerate(rows, 1):
            if vector_column not in row:
                die("{} row {} missing vector column {!r}".format(path, idx, vector_column))
            vectors.append(parse_vector(row[vector_column], "{} row {}".format(path, idx)))
    else:
        die("unsupported embedding format: {}".format(fmt))
    if not vectors:
        die("no embeddings loaded from {}".format(path))
    return vectors


def matrix_from_vectors(vectors, expected_rows, label):
    try:
        import numpy as np
    except Exception as exc:
        die("dense embedding mode requires numpy: {}".format(exc))
    if len(vectors) != expected_rows:
        die("{} count {} does not match text row count {}".format(label, len(vectors), expected_rows))
    dims = set(len(vec) for vec in vectors)
    if len(dims) != 1:
        die("{} vectors are ragged: dimensions {}".format(label, sorted(dims)))
    return np.asarray(vectors, dtype="float32")


def run_bm25(corpus, queries, top_k):
    try:
        from text2vec.utils.rank_bm25 import BM25Okapi
        from text2vec.utils.tokenizer import JiebaTokenizer
    except Exception as exc:
        die("BM25 mode requires text2vec with Jieba/rank_bm25 utilities installed: {}".format(exc))

    tokenizer = JiebaTokenizer()
    tokenized_corpus = [tokenizer.tokenize(doc, HMM=False) for doc in corpus]
    if not any(tokenized_corpus):
        die("BM25 corpus tokenization produced no tokens")
    scorer = BM25Okapi(tokenized_corpus)
    k = min(top_k, len(corpus))
    all_hits = []
    for query in queries:
        tokens = tokenizer.tokenize(query, HMM=False)
        scores = scorer.get_scores(tokens)
        order = sorted(range(len(corpus)), key=lambda idx: float(scores[idx]), reverse=True)[:k]
        hits = []
        for rank, corpus_id in enumerate(order, 1):
            hits.append({
                "rank": rank,
                "corpus_id": int(corpus_id),
                "corpus": corpus[corpus_id],
                "score": float(scores[corpus_id]),
            })
        all_hits.append(hits)
    return all_hits


def manual_dense_search(query_matrix, corpus_matrix, top_k):
    import numpy as np

    def normalize(matrix):
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        return matrix / norms

    q_norm = normalize(query_matrix)
    c_norm = normalize(corpus_matrix)
    scores = q_norm.dot(c_norm.T)
    k = min(top_k, corpus_matrix.shape[0])
    results = []
    for query_idx in range(scores.shape[0]):
        order = np.argsort(-scores[query_idx])[:k]
        results.append([
            {"corpus_id": int(corpus_id), "score": float(scores[query_idx, corpus_id])}
            for corpus_id in order
        ])
    return results


def semantic_dense_search(query_matrix, corpus_matrix, top_k):
    try:
        from text2vec import semantic_search
        return semantic_search(query_matrix, corpus_matrix, top_k=top_k)
    except Exception as exc:
        print("warning: text2vec.semantic_search unavailable; using local cosine fallback: {}".format(exc), file=sys.stderr)
        return manual_dense_search(query_matrix, corpus_matrix, top_k)


def encode_with_model(corpus, queries, args):
    try:
        from text2vec import SentenceModel
    except Exception as exc:
        die("failed to import text2vec SentenceModel: {}".format(exc))
    try:
        model = SentenceModel(
            model_name_or_path=args.model_name,
            max_seq_length=args.max_seq_length,
            device=args.device,
        )
    except Exception as exc:
        die(
            "failed to initialize SentenceModel with model {!r}: {}. "
            "Use precomputed embeddings for a no-network path.".format(args.model_name, exc)
        )
    try:
        corpus_matrix = model.encode(
            corpus,
            batch_size=args.batch_size,
            normalize_embeddings=args.normalize_embeddings,
        )
        query_matrix = model.encode(
            queries,
            batch_size=args.batch_size,
            normalize_embeddings=args.normalize_embeddings,
        )
    except Exception as exc:
        die("SentenceModel encoding failed: {}".format(exc))
    return corpus_matrix, query_matrix


def run_dense(corpus, queries, args):
    precomputed = args.corpus_embeddings_file is not None or args.query_embeddings_file is not None
    if precomputed:
        if args.corpus_embeddings_file is None or args.query_embeddings_file is None:
            die("dense precomputed mode needs both --corpus-embeddings-file and --query-embeddings-file")
        if args.model_name:
            print("warning: embedding files are present; --model-name will not be loaded", file=sys.stderr)
        corpus_vectors = load_embeddings(
            args.corpus_embeddings_file,
            infer_embedding_format(args.corpus_embeddings_file, args.embedding_format),
            args.embedding_column,
        )
        query_vectors = load_embeddings(
            args.query_embeddings_file,
            infer_embedding_format(args.query_embeddings_file, args.embedding_format),
            args.embedding_column,
        )
        corpus_matrix = matrix_from_vectors(corpus_vectors, len(corpus), "corpus embeddings")
        query_matrix = matrix_from_vectors(query_vectors, len(queries), "query embeddings")
    else:
        if not args.model_name:
            die("dense mode needs precomputed embeddings or --model-name")
        corpus_matrix, query_matrix = encode_with_model(corpus, queries, args)
        corpus_matrix = matrix_from_vectors([list(row) for row in corpus_matrix], len(corpus), "model corpus embeddings")
        query_matrix = matrix_from_vectors([list(row) for row in query_matrix], len(queries), "model query embeddings")

    if corpus_matrix.shape[1] != query_matrix.shape[1]:
        die("embedding dimension mismatch: corpus dim {} vs query dim {}".format(corpus_matrix.shape[1], query_matrix.shape[1]))
    return semantic_dense_search(query_matrix, corpus_matrix, args.top_k)


def open_output(path):
    if path is None:
        return sys.stdout, False
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("w", encoding="utf-8"), True


def write_results(output_file, mode, queries, corpus, all_hits):
    out_handle, should_close = open_output(output_file)
    try:
        for query_id, hits in enumerate(all_hits):
            enriched_hits = []
            for rank, hit in enumerate(hits, 1):
                corpus_id = int(hit["corpus_id"])
                enriched_hits.append({
                    "rank": rank,
                    "corpus_id": corpus_id,
                    "corpus": corpus[corpus_id],
                    "score": float(hit["score"]),
                })
            record = {
                "query_id": query_id,
                "query": queries[query_id],
                "mode": mode,
                "hits": enriched_hits,
            }
            out_handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    finally:
        if should_close:
            out_handle.close()


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Search a corpus with text2vec BM25 or dense cosine retrieval.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--mode", choices=("bm25", "dense"), default="bm25")
    parser.add_argument("--corpus-file", required=True, type=Path, help="Corpus text file; default format is one document per line.")
    parser.add_argument("--query-file", required=True, type=Path, help="Query text file; default format is one query per line.")
    parser.add_argument("--corpus-format", choices=("auto", "text", "jsonl", "csv", "tsv"), default="auto")
    parser.add_argument("--query-format", choices=("auto", "text", "jsonl", "csv", "tsv"), default="auto")
    parser.add_argument("--corpus-text-column", default="text")
    parser.add_argument("--query-text-column", default="text")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--output-file", type=Path, help="Write JSONL search results here. Defaults to stdout.")
    parser.add_argument("--corpus-embeddings-file", type=Path, help="Dense mode: precomputed corpus embeddings JSON/JSONL/CSV/TSV.")
    parser.add_argument("--query-embeddings-file", type=Path, help="Dense mode: precomputed query embeddings JSON/JSONL/CSV/TSV.")
    parser.add_argument("--embedding-format", choices=("auto", "json", "jsonl", "csv", "tsv"), default="auto")
    parser.add_argument("--embedding-column", default="embedding")
    parser.add_argument("--model-name", help="Dense mode: local/cached model path or public model ID. May download if not cached.")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--max-seq-length", type=int, default=256)
    parser.add_argument("--device", help="Optional torch device for model-backed dense encoding, such as cpu or cuda.")
    parser.add_argument("--normalize-embeddings", action="store_true", help="Ask SentenceModel.encode to normalize embeddings in model-backed mode.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    if args.top_k <= 0:
        die("--top-k must be positive")

    corpus = read_texts(
        args.corpus_file,
        infer_collection_format(args.corpus_file, args.corpus_format),
        args.corpus_text_column,
    )
    queries = read_texts(
        args.query_file,
        infer_collection_format(args.query_file, args.query_format),
        args.query_text_column,
    )

    if args.mode == "bm25":
        all_hits = run_bm25(corpus, queries, args.top_k)
    else:
        all_hits = run_dense(corpus, queries, args)
    write_results(args.output_file, args.mode, queries, corpus, all_hits)


if __name__ == "__main__":
    main()
