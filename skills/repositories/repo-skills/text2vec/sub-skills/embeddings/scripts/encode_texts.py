#!/usr/bin/env python3
"""Batch-encode newline-delimited text with text2vec.

The script intentionally imports text2vec lazily so ``--help`` works even when
heavy inference dependencies are not installed. It does not require a source
checkout; it uses the installed ``text2vec`` package APIs.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

DEFAULT_SENTENCE_MODEL = "shibing624/text2vec-base-chinese"
DEFAULT_WORD2VEC_MODEL = "w2v-light-tencent-chinese"
ENCODER_TYPES = ("FIRST_LAST_AVG", "LAST_AVG", "CLS", "POOLER", "MEAN")
MODEL_TYPES = ("sentencemodel", "sbert", "word2vec")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Encode one sentence per line with text2vec SentenceModel/SBert or Word2Vec.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input-file", "--input_file",
        dest="input_file",
        required=True,
        help="Input UTF-8 text file; each non-empty line is one sentence. Duplicates are preserved.",
    )
    parser.add_argument(
        "--output-file", "--output_file",
        dest="output_file",
        required=True,
        help="Output path. Use .csv for CSV or .jsonl/.ndjson for JSON lines.",
    )
    parser.add_argument(
        "--model-type", "--model_type",
        dest="model_type",
        choices=MODEL_TYPES,
        default="sentencemodel",
        help="Embedding backend. 'sbert' is an alias for SentenceModel.",
    )
    parser.add_argument(
        "--model-name", "--model_name",
        dest="model_name",
        default=None,
        help=(
            "Model id or local path. Default is %s for SentenceModel/SBert and %s for Word2Vec."
            % (DEFAULT_SENTENCE_MODEL, DEFAULT_WORD2VEC_MODEL)
        ),
    )
    parser.add_argument(
        "--encoder-type", "--encoder_type",
        dest="encoder_type",
        choices=ENCODER_TYPES,
        default="MEAN",
        help="SentenceModel pooling strategy. Ignored by Word2Vec.",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="PyTorch device for SentenceModel, such as cpu, cuda, cuda:0, or mps. Ignored by Word2Vec.",
    )
    parser.add_argument(
        "--batch-size", "--batch_size",
        dest="batch_size",
        type=int,
        default=32,
        help="Batch size for SentenceModel encode or multi-process encode.",
    )
    parser.add_argument(
        "--max-seq-length", "--max_seq_length",
        dest="max_seq_length",
        type=int,
        default=256,
        help="SentenceModel tokenizer truncation length. Ignored by Word2Vec.",
    )
    parser.add_argument(
        "--chunk-size", "--chunk_size",
        dest="chunk_size",
        type=int,
        default=1000,
        help="Number of input lines to encode per single-process chunk, or SentenceModel multi-process work chunk size.",
    )
    parser.add_argument(
        "--show-progress-bar", "--show_progress_bar",
        dest="show_progress_bar",
        action="store_true",
        help="Show text2vec/tqdm progress bars.",
    )
    parser.add_argument(
        "--normalize-embeddings", "--normalize_embeddings",
        dest="normalize_embeddings",
        action="store_true",
        help="L2-normalize SentenceModel embeddings before writing. Ignored by Word2Vec.",
    )
    parser.add_argument(
        "--multi-gpu", "--multi_gpu",
        dest="multi_gpu",
        action="store_true",
        help="Use SentenceModel start_multi_process_pool/encode_multi_process. Not supported for Word2Vec.",
    )
    parser.add_argument(
        "--word2vec-binary", "--word2vec_binary",
        dest="word2vec_binary",
        action="store_true",
        help="Treat a local Word2Vec file as binary. A .bin suffix is also auto-detected.",
    )
    return parser


def read_sentences(input_file):
    path = Path(input_file).expanduser()
    if not path.is_file():
        raise FileNotFoundError("Input file does not exist or is not a file: %s" % path)
    sentences = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if text:
                sentences.append(text)
    return sentences


def infer_output_format(output_file):
    suffix = Path(output_file).suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix in {".jsonl", ".ndjson"}:
        return "jsonl"
    raise ValueError("Output file must end with .csv, .jsonl, or .ndjson: %s" % output_file)


def iter_chunks(items, chunk_size):
    if chunk_size is None or chunk_size <= 0:
        chunk_size = len(items) or 1
    for start in range(0, len(items), chunk_size):
        yield items[start:start + chunk_size]


def embedding_to_list(vector):
    if hasattr(vector, "tolist"):
        value = vector.tolist()
    else:
        value = list(vector)
    if isinstance(value, tuple):
        value = list(value)
    return value


def write_records(output_file, output_format, sentences, embeddings):
    output_path = Path(output_file).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    row_count = 0
    if output_format == "csv":
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["sentence", "embedding"])
            writer.writeheader()
            for sentence, embedding in zip(sentences, embeddings):
                writer.writerow({
                    "sentence": sentence,
                    "embedding": json.dumps(embedding_to_list(embedding), ensure_ascii=False),
                })
                row_count += 1
    else:
        with output_path.open("w", encoding="utf-8") as handle:
            for sentence, embedding in zip(sentences, embeddings):
                record = {"sentence": sentence, "embedding": embedding_to_list(embedding)}
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                row_count += 1
    return row_count


def append_chunk_records(handle, output_format, writer, sentences, embeddings):
    row_count = 0
    for sentence, embedding in zip(sentences, embeddings):
        vector = embedding_to_list(embedding)
        if output_format == "csv":
            writer.writerow({"sentence": sentence, "embedding": json.dumps(vector, ensure_ascii=False)})
        else:
            handle.write(json.dumps({"sentence": sentence, "embedding": vector}, ensure_ascii=False) + "\n")
        row_count += 1
    return row_count


def sentence_model_help(exc):
    return (
        "Failed to load text2vec SentenceModel/SBert. Ensure the text2vec package is installed/importable. "
        "SentenceModel also requires torch, transformers, and a loadable HF-compatible model. "
        "For no-network runs, pass a complete local model directory. For remote model ids, ensure "
        "network/cache access. Original error: %s: %s"
        % (exc.__class__.__name__, exc)
    )


def word2vec_help(exc):
    return (
        "Failed to load text2vec Word2Vec. Ensure the text2vec package is installed/importable. "
        "Word2Vec also requires gensim and either an existing local word2vec-format file or a supported "
        "built-in key such as w2v-light-tencent-chinese. If a local file is binary, pass "
        "--word2vec-binary or use a .bin suffix. Original error: %s: %s"
        % (exc.__class__.__name__, exc)
    )


def load_sentence_model(args):
    try:
        from text2vec.sentence_model import SentenceModel
        return SentenceModel(
            model_name_or_path=args.model_name,
            encoder_type=args.encoder_type,
            max_seq_length=args.max_seq_length,
            device=args.device,
        )
    except Exception as exc:  # noqa: BLE001 - convert dependency/download errors into operator guidance.
        raise RuntimeError(sentence_model_help(exc)) from exc


def load_word2vec(args):
    try:
        from text2vec.word2vec import Word2Vec
        w2v_kwargs = {}
        model_path = Path(args.model_name).expanduser()
        if args.word2vec_binary or (model_path.is_file() and model_path.suffix.lower() == ".bin"):
            w2v_kwargs["binary"] = True
        return Word2Vec(args.model_name, w2v_kwargs=w2v_kwargs or None)
    except Exception as exc:  # noqa: BLE001 - convert optional dependency/download errors into operator guidance.
        raise RuntimeError(word2vec_help(exc)) from exc


def encode_single_process(model, model_type, sentences, args, output_file, output_format):
    output_path = Path(output_file).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    row_count = 0
    if output_format == "csv":
        handle = output_path.open("w", encoding="utf-8", newline="")
        writer = csv.DictWriter(handle, fieldnames=["sentence", "embedding"])
        writer.writeheader()
    else:
        handle = output_path.open("w", encoding="utf-8")
        writer = None

    try:
        for chunk in iter_chunks(sentences, args.chunk_size):
            if model_type in {"sentencemodel", "sbert"}:
                embeddings = model.encode(
                    chunk,
                    batch_size=args.batch_size,
                    show_progress_bar=args.show_progress_bar,
                    convert_to_numpy=True,
                    convert_to_tensor=False,
                    normalize_embeddings=args.normalize_embeddings,
                    max_seq_length=args.max_seq_length,
                )
            else:
                embeddings = model.encode(chunk, show_progress_bar=args.show_progress_bar)
            if len(embeddings) != len(chunk):
                raise RuntimeError(
                    "Embedding row-count mismatch for chunk: got %d vectors for %d sentences"
                    % (len(embeddings), len(chunk))
                )
            row_count += append_chunk_records(handle, output_format, writer, chunk, embeddings)
    finally:
        handle.close()
    return row_count


def encode_multi_process(model, sentences, args, output_file, output_format):
    pool = model.start_multi_process_pool()
    try:
        embeddings = model.encode_multi_process(
            sentences,
            pool,
            batch_size=args.batch_size,
            normalize_embeddings=args.normalize_embeddings,
            chunk_size=args.chunk_size,
        )
    finally:
        model.stop_multi_process_pool(pool)

    if len(embeddings) != len(sentences):
        raise RuntimeError(
            "Embedding row-count mismatch: got %d vectors for %d sentences"
            % (len(embeddings), len(sentences))
        )
    return write_records(output_file, output_format, sentences, embeddings)


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.model_type = args.model_type.lower()

    if args.model_name is None:
        args.model_name = DEFAULT_WORD2VEC_MODEL if args.model_type == "word2vec" else DEFAULT_SENTENCE_MODEL

    if args.batch_size <= 0:
        parser.error("--batch-size must be positive")
    if args.max_seq_length <= 0:
        parser.error("--max-seq-length must be positive")
    if args.multi_gpu and args.model_type == "word2vec":
        parser.error("--multi-gpu/--multi_gpu is only supported for SentenceModel/SBert, not Word2Vec")

    try:
        sentences = read_sentences(args.input_file)
        output_format = infer_output_format(args.output_file)
        if not sentences:
            raise ValueError("No non-empty input lines found in %s" % args.input_file)

        if args.model_type in {"sentencemodel", "sbert"}:
            model = load_sentence_model(args)
            if args.multi_gpu:
                row_count = encode_multi_process(model, sentences, args, args.output_file, output_format)
            else:
                row_count = encode_single_process(model, args.model_type, sentences, args, args.output_file, output_format)
        else:
            model = load_word2vec(args)
            row_count = encode_single_process(model, args.model_type, sentences, args, args.output_file, output_format)

        if row_count != len(sentences):
            raise RuntimeError(
                "Output row-count mismatch: wrote %d rows for %d input sentences"
                % (row_count, len(sentences))
            )
        print("Wrote %d embedding rows to %s" % (row_count, args.output_file), file=sys.stderr)
        return 0
    except Exception as exc:  # noqa: BLE001 - user-facing command line helper.
        print("encode_texts.py: error: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
