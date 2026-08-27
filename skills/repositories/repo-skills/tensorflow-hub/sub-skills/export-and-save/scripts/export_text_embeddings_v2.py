#!/usr/bin/env python3
# Adapted from the TensorFlow Hub text embedding exporter.
# SPDX-License-Identifier: Apache-2.0
"""Export a TensorFlow Hub-compatible TF2 text embedding SavedModel.

Input format: one whitespace-delimited token followed by numeric vector values
per line, for example:

    cat 1.11 2.56 3.45
    dog 1.0 2.0 3.0

The exported object is a callable TF2 SavedModel. With --verify, the script
reloads it through tensorflow_hub.load() and prints sample outputs.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from typing import Iterable, List, Optional, Sequence, Tuple

np = None  # Lazy import so --help does not need TensorFlow/NumPy startup.
tf = None


def _ensure_runtime_deps() -> None:
    """Imports TensorFlow and NumPy after argument parsing."""
    global np, tf
    if np is None:
        import numpy as _np  # pylint: disable=import-outside-toplevel

        np = _np
    if tf is None:
        import tensorflow as _tf  # pylint: disable=import-outside-toplevel

        tf = _tf


def _non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be >= 0")
    return parsed


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be > 0")
    return parsed


def parse_embedding_line(line: str, line_number: int) -> Tuple[str, List[float]]:
    """Parses one token/vector line with clear validation errors."""
    columns = line.split()
    if not columns:
        raise ValueError(
            f"Line {line_number}: blank lines are not valid embedding rows; "
            "remove the line or skip it with --num-lines-to-ignore."
        )
    token, value_columns = columns[0], columns[1:]
    if not value_columns:
        raise ValueError(
            f"Line {line_number}: token {token!r} has no vector values."
        )
    try:
        values = [float(column) for column in value_columns]
    except ValueError as exc:
        raise ValueError(
            f"Line {line_number}: could not parse vector values for token "
            f"{token!r}: {exc}"
        ) from exc
    return token, values


def load_embeddings(
    file_path: str,
    num_lines_to_ignore: int = 0,
    num_lines_to_use: Optional[int] = None,
) -> Tuple[List[str], "np.ndarray"]:
    """Loads a token/vector text file into vocabulary and embedding matrix."""
    _ensure_runtime_deps()
    if num_lines_to_ignore < 0:
        raise ValueError("num_lines_to_ignore must be >= 0")
    if num_lines_to_use is not None and num_lines_to_use <= 0:
        raise ValueError("num_lines_to_use must be > 0 when provided")

    vocabulary: List[str] = []
    embeddings: List[List[float]] = []
    embedding_dim: Optional[int] = None

    with tf.io.gfile.GFile(file_path, "r") as handle:
        for physical_line_number, line in enumerate(handle, start=1):
            if physical_line_number <= num_lines_to_ignore:
                continue
            if num_lines_to_use is not None and len(vocabulary) >= num_lines_to_use:
                break

            token, vector = parse_embedding_line(line, physical_line_number)
            if embedding_dim is None:
                embedding_dim = len(vector)
            elif embedding_dim != len(vector):
                raise ValueError(
                    "Inconsistent embedding dimension detected, "
                    f"{embedding_dim} != {len(vector)} for token {token!r} "
                    f"on line {physical_line_number}."
                )
            vocabulary.append(token)
            embeddings.append(vector)

    if embedding_dim is None:
        raise ValueError(
            "Embedding file produced no usable embedding rows after applying "
            "--num-lines-to-ignore and --num-lines-to-use."
        )

    return vocabulary, np.asarray(embeddings, dtype=np.float32)


def _write_vocabulary_file(vocabulary: Iterable[str], directory: str) -> str:
    """Writes vocabulary tokens to a temporary file used as a SavedModel asset."""
    _ensure_runtime_deps()
    vocabulary_file = os.path.join(directory, "tokens.txt")
    with tf.io.gfile.GFile(vocabulary_file, "w") as handle:
        for token in vocabulary:
            handle.write(token + "\n")
    return vocabulary_file


def _build_text_embedding_model_class():
    """Builds the TensorFlow class after TensorFlow has been imported."""
    _ensure_runtime_deps()

    class TextEmbeddingModel(tf.train.Checkpoint):
        """Callable SavedModel that embeds batches of text strings."""

        def __init__(self, vocabulary_file: str, vectors, num_oov_buckets: int):
            super().__init__()
            self._num_oov_buckets = int(num_oov_buckets)
            self._table_initializer = tf.lookup.TextFileInitializer(
                vocabulary_file,
                tf.string,
                tf.lookup.TextFileIndex.WHOLE_LINE,
                tf.int64,
                tf.lookup.TextFileIndex.LINE_NUMBER,
            )
            self._table = tf.lookup.StaticVocabularyTable(
                self._table_initializer, num_oov_buckets=self._num_oov_buckets
            )

            vectors = np.asarray(vectors, dtype=np.float32)
            if self._num_oov_buckets:
                oov_rows = np.zeros(
                    [self._num_oov_buckets, vectors.shape[1]], dtype=np.float32
                )
                vectors = np.concatenate([vectors, oov_rows], axis=0)

            self.embeddings = tf.Variable(
                vectors, trainable=True, dtype=tf.float32, name="embeddings"
            )
            # Preserve the conventions understood by tensorflow_hub.KerasLayer.
            self.variables = [self.embeddings]
            self.trainable_variables = [self.embeddings]

        @tf.function(input_signature=[tf.TensorSpec([None], tf.string, name="sentences")])
        def _tokenize(self, sentences):
            normalized = tf.strings.regex_replace(
                input=sentences, pattern=r"\pP", rewrite=""
            )
            normalized = tf.reshape(normalized, [-1])
            sparse_tokens = tf.strings.split(normalized, " ").to_sparse()

            # Handle one or more empty rows, including the all-empty batch case.
            sparse_tokens, _ = tf.sparse.fill_empty_rows(
                sparse_tokens, tf.constant("")
            )
            sparse_tokens = tf.sparse.reset_shape(sparse_tokens)
            token_ids = self._table.lookup(sparse_tokens.values)
            return sparse_tokens.indices, token_ids, sparse_tokens.dense_shape

        @tf.function(input_signature=[tf.TensorSpec([None], tf.string, name="sentences")])
        def __call__(self, sentences):
            token_indices, token_ids, token_dense_shape = self._tokenize(sentences)
            return tf.nn.safe_embedding_lookup_sparse(
                embedding_weights=self.embeddings,
                sparse_ids=tf.SparseTensor(token_indices, token_ids, token_dense_shape),
                sparse_weights=None,
                combiner="sqrtn",
            )

    return TextEmbeddingModel


def _check_export_path(export_path: str) -> None:
    """Refuses accidental overwrite of non-empty output paths."""
    _ensure_runtime_deps()
    if tf.io.gfile.exists(export_path):
        if not tf.io.gfile.isdir(export_path):
            raise FileExistsError(f"Export path exists and is not a directory: {export_path}")
        existing = tf.io.gfile.listdir(export_path)
        if existing:
            preview = ", ".join(sorted(existing)[:5])
            raise FileExistsError(
                "Export path already exists and is not empty: "
                f"{export_path} (contains: {preview})"
            )


def export_module_from_file(
    embedding_file: str,
    export_path: str,
    num_oov_buckets: int = 1,
    num_lines_to_ignore: int = 0,
    num_lines_to_use: Optional[int] = None,
):
    """Exports a callable TF2 SavedModel from a token/vector file."""
    _ensure_runtime_deps()
    if num_oov_buckets < 0:
        raise ValueError("num_oov_buckets must be >= 0")
    _check_export_path(export_path)

    vocabulary, vectors = load_embeddings(
        embedding_file,
        num_lines_to_ignore=num_lines_to_ignore,
        num_lines_to_use=num_lines_to_use,
    )
    TextEmbeddingModel = _build_text_embedding_model_class()
    with tempfile.TemporaryDirectory(prefix="tfhub_text_embedding_vocab_") as temp_dir:
        vocabulary_file = _write_vocabulary_file(vocabulary, temp_dir)
        module = TextEmbeddingModel(vocabulary_file, vectors, num_oov_buckets)
        tf.saved_model.save(module, export_path)

    return {
        "vocabulary": vocabulary,
        "vocabulary_size": len(vocabulary),
        "embedding_dim": int(vectors.shape[1]),
        "num_oov_buckets": int(num_oov_buckets),
    }


def _flatten_sample_text(groups: Optional[Sequence[Sequence[str]]]) -> List[str]:
    samples: List[str] = []
    for group in groups or []:
        samples.extend(group)
    return samples


def _default_samples(vocabulary: Sequence[str]) -> List[str]:
    if not vocabulary:
        return ["", "__unknown_token__"]
    first = vocabulary[0]
    if len(vocabulary) > 1:
        second = vocabulary[1]
        return [first, f"{first} {second}", "__unknown_token__", ""]
    return [first, f"{first} {first}", "__unknown_token__", ""]


def verify_export(export_path: str, sample_texts: Sequence[str]):
    """Reloads the exported SavedModel with tensorflow_hub.load and prints outputs."""
    _ensure_runtime_deps()
    try:
        import tensorflow_hub as hub  # pylint: disable=import-outside-toplevel
    except ImportError as exc:
        raise RuntimeError(
            "--verify requires tensorflow_hub to be installed in this Python environment."
        ) from exc

    loaded = hub.load(export_path)
    if not callable(loaded):
        signatures = getattr(loaded, "signatures", {})
        raise TypeError(
            "The exported SavedModel loaded successfully but is not directly callable. "
            f"Available signatures: {list(signatures.keys())}"
        )

    sample_tensor = tf.constant(list(sample_texts), dtype=tf.string)
    outputs = loaded(sample_tensor)
    print("Verification via tensorflow_hub.load: ok")
    print(f"sample_texts={list(sample_texts)!r}")
    print(f"output_shape={outputs.shape.as_list()}")
    print(f"outputs={outputs.numpy().tolist()!r}")
    return outputs


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export a callable TF2 SavedModel text embedder from a whitespace "
            "token/vector file."
        )
    )
    parser.add_argument(
        "--embedding-file",
        required=True,
        help="Path to a text file with one token followed by numeric vector values per line.",
    )
    parser.add_argument(
        "--export-path",
        required=True,
        help="New or empty directory where the SavedModel will be written.",
    )
    parser.add_argument(
        "--num-oov-buckets",
        type=_non_negative_int,
        default=1,
        help="Number of out-of-vocabulary buckets to append. Default: 1.",
    )
    parser.add_argument(
        "--num-lines-to-ignore",
        type=_non_negative_int,
        default=0,
        help="Number of initial lines to skip before parsing embeddings. Default: 0.",
    )
    parser.add_argument(
        "--num-lines-to-use",
        type=_positive_int,
        default=None,
        help="Maximum number of embedding rows to use after skipped lines. Default: all.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Reload the SavedModel with tensorflow_hub.load and print sample outputs.",
    )
    parser.add_argument(
        "--sample-text",
        action="append",
        nargs="+",
        metavar="TEXT",
        help=(
            "Sample text for --verify. Repeat the flag or pass multiple values; "
            "quote samples that contain spaces."
        ),
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        info = export_module_from_file(
            embedding_file=args.embedding_file,
            export_path=args.export_path,
            num_oov_buckets=args.num_oov_buckets,
            num_lines_to_ignore=args.num_lines_to_ignore,
            num_lines_to_use=args.num_lines_to_use,
        )
        print(f"SavedModel exported to: {args.export_path}")
        print(
            "vocabulary_size={vocabulary_size} embedding_dim={embedding_dim} "
            "num_oov_buckets={num_oov_buckets}".format(**info)
        )

        if args.verify:
            samples = _flatten_sample_text(args.sample_text)
            if not samples:
                samples = _default_samples(info["vocabulary"])
            verify_export(args.export_path, samples)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
