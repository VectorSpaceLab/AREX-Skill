#!/usr/bin/env python3
"""Score aligned sentence pairs with text2vec-safe workflows.

The script has two modes:
  1. no-network vector mode from inline vector columns or an embedding lookup file;
  2. model mode with text2vec.Similarity when --model-name is supplied.

It always emits one score per input row. It never builds a cross-product matrix.
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


def infer_table_format(path, requested):
    if requested != "auto":
        return requested
    suffix = path.suffix.lower()
    if suffix in (".jsonl", ".ndjson"):
        return "jsonl"
    if suffix == ".tsv":
        return "tsv"
    return "csv"


def infer_embedding_format(path, requested):
    if requested != "auto":
        return requested
    suffix = path.suffix.lower()
    if suffix == ".json":
        return "json"
    if suffix in (".jsonl", ".ndjson"):
        return "jsonl"
    if suffix == ".tsv":
        return "tsv"
    return "csv"


def read_jsonl(path):
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
            if not isinstance(item, dict):
                die("{}:{} must be a JSON object".format(path, line_no))
            rows.append(item)
    return rows


def read_delimited(path, delimiter):
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        if not reader.fieldnames:
            die("{} must have a header row".format(path))
        return [dict(row) for row in reader]


def read_rows(path, fmt):
    if not path.exists():
        die("input file does not exist: {}".format(path))
    if fmt == "jsonl":
        rows = read_jsonl(path)
    elif fmt == "csv":
        rows = read_delimited(path, ",")
    elif fmt == "tsv":
        rows = read_delimited(path, "\t")
    else:
        die("unsupported input format: {}".format(fmt))
    if not rows:
        die("input file has no rows: {}".format(path))
    return rows


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


def cosine_pair(vec1, vec2, context):
    if len(vec1) != len(vec2):
        die("dimension mismatch in {}: {} vs {}".format(context, len(vec1), len(vec2)))
    numerator = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return numerator / (norm1 * norm2)


def load_embedding_map(path, fmt, id_column, vector_column):
    if not path.exists():
        die("embedding file does not exist: {}".format(path))
    mapping = {}

    if fmt == "json":
        with path.open("r", encoding="utf-8") as handle:
            try:
                data = json.load(handle)
            except json.JSONDecodeError as exc:
                die("{} is not valid JSON: {}".format(path, exc))
        if isinstance(data, dict) and "embeddings" in data:
            data = data["embeddings"]
        if isinstance(data, dict):
            for key, value in data.items():
                mapping[str(key)] = parse_vector(value, "{}[{}]".format(path, key))
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                if isinstance(item, dict):
                    if id_column not in item or vector_column not in item:
                        die("embedding JSON item {} needs columns {!r} and {!r}".format(idx, id_column, vector_column))
                    key = item[id_column]
                    value = item[vector_column]
                else:
                    key = str(idx)
                    value = item
                mapping[str(key)] = parse_vector(value, "{}[{}]".format(path, key))
        else:
            die("embedding JSON must be a mapping or list")
    elif fmt in ("jsonl", "csv", "tsv"):
        rows = read_rows(path, fmt)
        for idx, row in enumerate(rows, 1):
            if id_column not in row or vector_column not in row:
                die("embedding row {} needs columns {!r} and {!r}".format(idx, id_column, vector_column))
            key = row[id_column]
            mapping[str(key)] = parse_vector(row[vector_column], "{} row {}".format(path, idx))
    else:
        die("unsupported embedding format: {}".format(fmt))

    if not mapping:
        die("embedding file produced an empty mapping: {}".format(path))
    return mapping


def has_value(row, key):
    return key in row and row[key] is not None and str(row[key]).strip() != ""


def vectors_for_row(row, row_index, args, embedding_map):
    if has_value(row, args.embedding1_column) and has_value(row, args.embedding2_column):
        vec1 = parse_vector(row[args.embedding1_column], "row {} column {}".format(row_index, args.embedding1_column))
        vec2 = parse_vector(row[args.embedding2_column], "row {} column {}".format(row_index, args.embedding2_column))
        return vec1, vec2, "inline-vector-cosine"

    if embedding_map is not None:
        if not has_value(row, args.id1_column) or not has_value(row, args.id2_column):
            die("row {} needs ID columns {!r} and {!r} for --embedding-file".format(row_index, args.id1_column, args.id2_column))
        key1 = str(row[args.id1_column])
        key2 = str(row[args.id2_column])
        if key1 not in embedding_map:
            die("row {} references missing embedding ID {!r}".format(row_index, key1))
        if key2 not in embedding_map:
            die("row {} references missing embedding ID {!r}".format(row_index, key2))
        return embedding_map[key1], embedding_map[key2], "embedding-file-cosine"

    return None, None, None


def build_similarity(args):
    try:
        from text2vec import EmbeddingType, Similarity, SimilarityType
    except Exception as exc:
        die("failed to import text2vec Similarity: {}".format(exc))

    sim_type = SimilarityType.COSINE if args.similarity_type == "cosine" else SimilarityType.WMD
    emb_type = EmbeddingType.BERT if args.embedding_type == "bert" else EmbeddingType.WORD2VEC
    try:
        return Similarity(
            model_name_or_path=args.model_name,
            similarity_type=sim_type,
            embedding_type=emb_type,
            max_seq_length=args.max_seq_length,
        )
    except Exception as exc:
        die(
            "failed to initialize text2vec Similarity with model {!r}: {}. "
            "Use a local/cached model path or omit --model-name and provide vector columns.".format(args.model_name, exc)
        )


def open_output(path):
    if path is None:
        return sys.stdout, False
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("w", encoding="utf-8"), True


def make_result(row, row_index, score, method, args):
    result = {
        "row": row_index,
        args.score_field: float(score),
        "method": method,
    }
    if has_value(row, args.text1_column):
        result["sentence1"] = row[args.text1_column]
    if has_value(row, args.text2_column):
        result["sentence2"] = row[args.text2_column]
    if has_value(row, args.id1_column):
        result["id1"] = row[args.id1_column]
    if has_value(row, args.id2_column):
        result["id2"] = row[args.id2_column]
    if has_value(row, "pair_id"):
        result["pair_id"] = row["pair_id"]
    return result


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Score aligned text pairs with supplied vectors or text2vec Similarity.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input-file", required=True, type=Path, help="JSONL, CSV, or TSV file with one pair per row.")
    parser.add_argument("--input-format", choices=("auto", "jsonl", "csv", "tsv"), default="auto")
    parser.add_argument("--output-file", type=Path, help="Write JSONL scores here. Defaults to stdout.")
    parser.add_argument("--text1-column", default="sentence1")
    parser.add_argument("--text2-column", default="sentence2")
    parser.add_argument("--embedding1-column", default="embedding1", help="Inline vector column for the first side.")
    parser.add_argument("--embedding2-column", default="embedding2", help="Inline vector column for the second side.")
    parser.add_argument("--embedding-file", type=Path, help="Optional embedding lookup file keyed by ID columns.")
    parser.add_argument("--embedding-format", choices=("auto", "json", "jsonl", "csv", "tsv"), default="auto")
    parser.add_argument("--embedding-id-column", default="id")
    parser.add_argument("--embedding-vector-column", default="embedding")
    parser.add_argument("--id1-column", default="id1")
    parser.add_argument("--id2-column", default="id2")
    parser.add_argument("--model-name", help="Local/cached model path or public model ID for text2vec Similarity.")
    parser.add_argument("--embedding-type", choices=("bert", "word2vec"), default="bert")
    parser.add_argument("--similarity-type", choices=("cosine", "wmd"), default="cosine")
    parser.add_argument("--max-seq-length", type=int, default=256)
    parser.add_argument("--score-field", default="score")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    rows = read_rows(args.input_file, infer_table_format(args.input_file, args.input_format))

    embedding_map = None
    if args.embedding_file is not None:
        embedding_map = load_embedding_map(
            args.embedding_file,
            infer_embedding_format(args.embedding_file, args.embedding_format),
            args.embedding_id_column,
            args.embedding_vector_column,
        )

    inline_vectors_present = any(
        has_value(row, args.embedding1_column) or has_value(row, args.embedding2_column)
        for row in rows
    )
    vector_mode = embedding_map is not None or inline_vectors_present

    if vector_mode and args.model_name:
        print("warning: vector inputs are present; --model-name will not be loaded", file=sys.stderr)

    if not vector_mode and not args.model_name:
        die("provide inline vectors, --embedding-file, or --model-name")

    similarity = None if vector_mode else build_similarity(args)

    out_handle, should_close = open_output(args.output_file)
    try:
        for row_index, row in enumerate(rows, 1):
            if vector_mode:
                vec1, vec2, method = vectors_for_row(row, row_index, args, embedding_map)
                if vec1 is None or vec2 is None:
                    die("row {} does not contain usable vector inputs".format(row_index))
                score = cosine_pair(vec1, vec2, "row {}".format(row_index))
            else:
                if not has_value(row, args.text1_column) or not has_value(row, args.text2_column):
                    die("row {} needs text columns {!r} and {!r}".format(row_index, args.text1_column, args.text2_column))
                try:
                    score = similarity.get_score(row[args.text1_column], row[args.text2_column])
                except Exception as exc:
                    die("Similarity scoring failed at row {}: {}".format(row_index, exc))
                method = "text2vec-similarity"

            result = make_result(row, row_index, score, method, args)
            out_handle.write(json.dumps(result, ensure_ascii=False) + "\n")
    finally:
        if should_close:
            out_handle.close()


if __name__ == "__main__":
    main()
