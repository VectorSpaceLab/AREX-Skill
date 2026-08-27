#!/usr/bin/env python3
"""Train a tiny scratch textgenrnn model and verify the saved artifacts."""

from __future__ import annotations

import argparse
import csv
import os
import random
import re
import shutil
import tempfile
from pathlib import Path

BASE_ROWS = [
    ("alpha beta gamma delta epsilon zeta eta theta iota kappa lambda.", "letters"),
    ("one two three four five six seven eight nine ten eleven twelve.", "numbers"),
    ("red blue green yellow orange purple black white silver gold cyan.", "colors"),
    ("sun moon star cloud river forest mountain valley ocean desert meadow.", "nature"),
]

DEFAULT_NAME = "textgenrnn_tiny_smoke"


def positive_int(raw: str) -> int:
    value = int(raw)
    if value <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return value


def sanitize_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._-")
    return cleaned or DEFAULT_NAME


def estimate_sequence_count(rows, word_level: bool) -> int:
    if word_level:
        return sum(len(text.split()) + 1 for text, _ in rows)
    return sum(len(text) + 1 for text, _ in rows)


def build_rows(word_level: bool, batch_size: int):
    rows = list(BASE_ROWS)
    target = max(batch_size * 4, 32)
    while estimate_sequence_count(rows, word_level) < target:
        rows.extend(rows)
    return rows


def write_fixture_file(workdir: Path, context: bool, word_level: bool, batch_size: int):
    rows = build_rows(word_level=word_level, batch_size=batch_size)
    if context:
        fixture_path = workdir / "tiny_context.csv"
        with fixture_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["text", "label"])
            for text, label in rows:
                writer.writerow([text, label])
    else:
        fixture_path = workdir / "tiny_training.txt"
        with fixture_path.open("w", encoding="utf-8") as handle:
            handle.write("text\n")
            handle.write("\n".join(text for text, _ in rows))
    return fixture_path


def load_textgenrnn_class():
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    try:
        from textgenrnn import textgenrnn
    except Exception as exc:  # pragma: no cover - import failure is environment-specific
        raise SystemExit(
            "Unable to import textgenrnn: "
            f"{exc}. Use ../../references/installation-and-compatibility.md "
            "and a pre-Keras-3 TensorFlow stack."
        ) from exc
    return textgenrnn


def seed_everything(seed: int = 0) -> None:
    random.seed(seed)
    try:
        import tensorflow as tf

        tf.random.set_seed(seed)
    except Exception:
        pass


def parse_args():
    parser = argparse.ArgumentParser(
        description="Train a tiny textgenrnn scratch model and verify the saved artifacts.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=None,
        help="Directory to write the fixture and training artifacts into.",
    )
    parser.add_argument(
        "--keep-artifacts",
        action="store_true",
        help="Keep the auto-created workdir after a successful run.",
    )
    parser.add_argument(
        "--context",
        action="store_true",
        help="Create a two-column context CSV and train with context labels.",
    )
    parser.add_argument(
        "--word-level",
        action="store_true",
        help="Train a word-level model instead of a character-level model.",
    )
    parser.add_argument(
        "--num-epochs",
        type=positive_int,
        default=1,
        help="Number of training epochs to run.",
    )
    parser.add_argument(
        "--batch-size",
        type=positive_int,
        default=2,
        help="Training batch size for the tiny fixture.",
    )
    parser.add_argument(
        "--max-length",
        type=positive_int,
        default=10,
        help="Sequence length used for the scratch model.",
    )
    parser.add_argument(
        "--rnn-size",
        type=positive_int,
        default=8,
        help="Number of recurrent units per LSTM layer.",
    )
    parser.add_argument(
        "--rnn-layers",
        type=positive_int,
        default=1,
        help="Number of LSTM layers for the scratch model.",
    )
    parser.add_argument(
        "--dim-embeddings",
        type=positive_int,
        default=8,
        help="Embedding dimension for the scratch model.",
    )
    parser.add_argument(
        "--name",
        default=DEFAULT_NAME,
        help="Artifact prefix for the saved model files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    name = sanitize_name(args.name)
    textgenrnn = load_textgenrnn_class()
    seed_everything()

    auto_created = args.workdir is None
    if args.workdir is None:
        workdir = Path(tempfile.mkdtemp(prefix="textgenrnn-train-smoke-"))
    else:
        workdir = args.workdir.expanduser().resolve()
        workdir.mkdir(parents=True, exist_ok=True)

    original_cwd = Path.cwd()
    try:
        os.chdir(workdir)
        fixture_path = write_fixture_file(
            workdir=workdir,
            context=args.context,
            word_level=args.word_level,
            batch_size=args.batch_size,
        )

        model = textgenrnn(name=name)
        train_kwargs = dict(
            num_epochs=args.num_epochs,
            gen_epochs=0,
            validation=False,
            verbose=0,
            batch_size=args.batch_size,
            max_length=args.max_length,
            rnn_size=args.rnn_size,
            rnn_layers=args.rnn_layers,
            dim_embeddings=args.dim_embeddings,
            word_level=args.word_level,
        )
        if args.context:
            model.train_from_file(
                str(fixture_path),
                new_model=True,
                context=True,
                **train_kwargs,
            )
        else:
            model.train_from_file(
                str(fixture_path),
                new_model=True,
                **train_kwargs,
            )

        artifact_names = [
            f"{name}_config.json",
            f"{name}_vocab.json",
            f"{name}_weights.hdf5",
        ]
        for artifact_name in artifact_names:
            artifact_path = workdir / artifact_name
            if not artifact_path.exists() or artifact_path.stat().st_size <= 0:
                raise SystemExit(f"Missing expected artifact: {artifact_name}")

        print("Smoke training complete.")
        print("Artifacts:")
        for artifact_name in artifact_names:
            print(f"- {artifact_name}")
        return 0
    finally:
        os.chdir(original_cwd)
        if auto_created and not args.keep_artifacts:
            shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
