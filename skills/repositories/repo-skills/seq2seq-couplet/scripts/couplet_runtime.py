"""Shared helpers for the seq2seq-couplet bundled scripts.

Purpose:
- use the bundled runtime copy by default so helpers are self-contained;
- optionally inspect a live checkout when ``--repo-root`` is supplied;
- generate tiny aligned fixtures for smoke tests;
- train a tiny checkpoint for verification;
- build the Flask inference app without importing the legacy source server file.

These helpers are safe to import from the bundled scripts in this skill tree.
They never assume a fixed checkout path.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

SPLIT_CHARS = ["，", "、", ",", ".", "。", "!", "！", "?", "？", " "]
DEFAULT_VOCAB = ["<s>", "</s>", "天", "地", "风", "云", "山", "水"]
DEFAULT_TRAIN_PAIRS = [("天 地", "风 云"), ("山 水", "风 山")]
DEFAULT_TEST_PAIRS = [("天 地", "风 云")]


def add_repo_root(repo_root: Union[str, Path]) -> Path:
    """Add a repository checkout to ``sys.path`` and return the resolved path."""

    repo_root = Path(repo_root).expanduser().resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    return repo_root


def import_repo_modules(repo_root: Optional[Union[str, Path]] = None):
    """Import and return the modules used by the bundled wrappers.

    By default this imports the self-contained runtime copy packaged inside the
    skill. Supplying ``repo_root`` is only for comparing or smoke-checking a live
    checkout.
    """

    if repo_root:
        add_repo_root(repo_root)
        bleu = importlib.import_module("bleu")
        reader = importlib.import_module("reader")
        seq2seq = importlib.import_module("seq2seq")
        model = importlib.import_module("model")
    else:
        runtime = importlib.import_module("runtime")
        bleu = importlib.import_module("runtime.bleu")
        reader = importlib.import_module("runtime.reader")
        seq2seq = importlib.import_module("runtime.seq2seq")
        model = importlib.import_module("runtime.model")
        _ = runtime
    return {
        "bleu": bleu,
        "reader": reader,
        "seq2seq": seq2seq,
        "model": model,
    }


def ensure_parent_dir(path: Union[str, Path]) -> Path:
    path = Path(path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_lines(path: Union[str, Path], lines: Sequence[str]) -> Path:
    path = ensure_parent_dir(path)
    text = "\n".join(lines)
    if lines:
        text += "\n"
    path.write_text(text, encoding="utf-8")
    return path


def validate_vocab_file(vocab_file: Union[str, Path]) -> List[str]:
    """Return the vocabulary lines and ensure the required special-token order."""

    vocab_file = Path(vocab_file)
    vocab = [line.rstrip("\n") for line in vocab_file.read_text(encoding="utf-8").splitlines()]
    if len(vocab) < 2:
        raise ValueError("vocab file must contain at least <s> and </s>")
    if vocab[0] != "<s>" or vocab[1] != "</s>":
        raise ValueError("vocab file must place <s> first and </s> second")
    return vocab


def _read_token_lines(path: Union[str, Path]) -> List[List[str]]:
    path = Path(path)
    return [[token for token in line.strip().split(" ") if token] for line in path.read_text(encoding="utf-8").splitlines()]


def validate_parallel_files(
    input_file: Union[str, Path],
    target_file: Union[str, Path],
    vocab_file: Union[str, Path],
    batch_size: int,
) -> Dict[str, object]:
    """Validate one aligned input/target pair before TensorFlow graph build."""

    vocab = validate_vocab_file(vocab_file)
    vocab_set = set(vocab)
    input_rows = _read_token_lines(input_file)
    target_rows = _read_token_lines(target_file)
    errors: List[str] = []
    warnings: List[str] = []

    if len(input_rows) != len(target_rows):
        errors.append(
            "input/target line count mismatch: %s vs %s" % (len(input_rows), len(target_rows))
        )
    usable_rows = min(len(input_rows), len(target_rows))
    if usable_rows == 0:
        errors.append("no usable aligned rows")
    if batch_size <= 0:
        errors.append("batch_size must be positive")
    elif usable_rows and batch_size > usable_rows:
        errors.append(
            "batch_size %s exceeds usable row count %s; SeqReader.data_size would be 0"
            % (batch_size, usable_rows)
        )
    elif usable_rows and usable_rows % batch_size != 0:
        warnings.append(
            "usable row count %s is not divisible by batch_size %s; SeqReader drops the tail"
            % (usable_rows, batch_size)
        )

    unknown_input = sum(1 for row in input_rows for token in row if token not in vocab_set)
    unknown_target = sum(1 for row in target_rows for token in row if token not in vocab_set)
    if unknown_input or unknown_target:
        warnings.append(
            "unknown tokens will be silently dropped: input=%s target=%s"
            % (unknown_input, unknown_target)
        )

    return {
        "input_file": str(Path(input_file)),
        "target_file": str(Path(target_file)),
        "input_rows": len(input_rows),
        "target_rows": len(target_rows),
        "usable_rows": usable_rows,
        "batch_size": batch_size,
        "unknown_input_tokens": unknown_input,
        "unknown_target_tokens": unknown_target,
        "errors": errors,
        "warnings": warnings,
    }


def write_tiny_fixture(
    workdir: Union[str, Path],
    *,
    vocab: Sequence[str] = DEFAULT_VOCAB,
    train_pairs: Sequence[Tuple[str, str]] = DEFAULT_TRAIN_PAIRS,
    test_pairs: Sequence[Tuple[str, str]] = DEFAULT_TEST_PAIRS,
) -> Dict[str, Path]:
    """Create a deterministic tiny dataset and return the generated file paths."""

    workdir = Path(workdir).expanduser().resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    train_input = workdir / "train.in.txt"
    train_target = workdir / "train.out.txt"
    test_input = workdir / "test.in.txt"
    test_target = workdir / "test.out.txt"
    vocab_file = workdir / "vocabs.txt"

    write_lines(vocab_file, list(vocab))
    write_lines(train_input, [left for left, _ in train_pairs])
    write_lines(train_target, [right for _, right in train_pairs])
    write_lines(test_input, [left for left, _ in test_pairs])
    write_lines(test_target, [right for _, right in test_pairs])

    return {
        "workdir": workdir,
        "train_input": train_input,
        "train_target": train_target,
        "test_input": test_input,
        "test_target": test_target,
        "vocab_file": vocab_file,
    }


def build_model(
    repo_root: Optional[Union[str, Path]],
    *,
    train_input_file: Optional[Union[str, Path]],
    train_target_file: Optional[Union[str, Path]],
    test_input_file: Optional[Union[str, Path]],
    test_target_file: Optional[Union[str, Path]],
    vocab_file: Union[str, Path],
    num_units: int,
    layers: int,
    dropout: float,
    batch_size: int,
    learning_rate: float,
    output_dir: Union[str, Path],
    save_step: int = 100,
    eval_step: int = 1000,
    param_histogram: bool = False,
    restore_model: bool = False,
    init_train: bool = True,
    init_infer: bool = False,
):
    """Instantiate the repo's ``Model`` class with explicit paths."""

    modules = import_repo_modules(repo_root)
    model_mod = modules["model"]
    output_dir = Path(output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    return model_mod.Model(
        str(train_input_file) if train_input_file is not None else None,
        str(train_target_file) if train_target_file is not None else None,
        str(test_input_file) if test_input_file is not None else None,
        str(test_target_file) if test_target_file is not None else None,
        str(vocab_file),
        num_units=num_units,
        layers=layers,
        dropout=dropout,
        batch_size=batch_size,
        learning_rate=learning_rate,
        output_dir=str(output_dir),
        save_step=save_step,
        eval_step=eval_step,
        param_histogram=param_histogram,
        restore_model=restore_model,
        init_train=init_train,
        init_infer=init_infer,
    )


def train_tiny_checkpoint(
    repo_root: Optional[Union[str, Path]],
    workdir: Union[str, Path],
    *,
    num_units: int = 16,
    layers: int = 2,
    dropout: float = 0.0,
    batch_size: int = 1,
    learning_rate: float = 0.01,
    epochs: int = 1,
) -> Dict[str, Path]:
    """Train a tiny checkpoint and return the files needed by smoke tests."""

    fixture = write_tiny_fixture(workdir)
    output_dir = Path(workdir).expanduser().resolve() / "output"
    model = build_model(
        repo_root,
        train_input_file=fixture["train_input"],
        train_target_file=fixture["train_target"],
        test_input_file=fixture["test_input"],
        test_target_file=fixture["test_target"],
        vocab_file=fixture["vocab_file"],
        num_units=num_units,
        layers=layers,
        dropout=dropout,
        batch_size=batch_size,
        learning_rate=learning_rate,
        output_dir=output_dir,
        save_step=1,
        eval_step=1000,
        param_histogram=False,
        restore_model=False,
        init_train=True,
        init_infer=False,
    )
    # Start at step 1 so the legacy train loop does not immediately run the
    # beam-search evaluation branch at step 0. The smoke verifies training and
    # checkpoint creation, not BLEU quality.
    first_step = 1
    model.train(first_step + max(epochs, 1), start=first_step)
    return {
        **fixture,
        "output_dir": output_dir,
        "model": model,
    }


def load_censor_words(censor_words_file: Optional[Union[str, Path]]) -> List[str]:
    if censor_words_file is None:
        return []
    path = Path(censor_words_file)
    if not path.exists():
        raise FileNotFoundError(f"censor words file not found: {path}")
    return [line.rstrip("\n") for line in path.read_text(encoding="utf-8").splitlines() if line.rstrip("\n")]


def all_same(text: str) -> bool:
    if len(text) <= 1:
        return True
    first = text[0]
    for char in text[1:]:
        if char not in SPLIT_CHARS and char != first:
            return False
    return True


def manual_correct_result(
    in_str: str,
    outputs: Sequence[str],
    scores: Sequence[float],
    *,
    censor_words: Sequence[str] = (),
) -> Tuple[List[str], List[float]]:
    """Replicate the legacy service's post-processing heuristics."""

    adjusted_scores = list(scores)
    adjusted_outputs = list(outputs)
    is_all_same = all_same(in_str)

    for i, output in enumerate(adjusted_outputs):
        if is_all_same:
            adjusted_scores[i] -= 100
            continue
        adjusted_scores[i] -= abs(len(in_str) - len(output))
        length = min(len(in_str), len(output))
        for censor_word in censor_words:
            if censor_word and (censor_word in in_str or censor_word in output):
                adjusted_scores[i] -= 1000
                break
        for j in range(length):
            for k in range(j, length):
                if (in_str[j] == in_str[k]) != (output[j] == output[k]):
                    adjusted_scores[i] -= 10
        for j in range(length):
            for k in range(length):
                if output[k] not in SPLIT_CHARS and in_str[j] == output[k]:
                    adjusted_scores[i] -= 10
        if length > 0:
            adjusted_scores[i] = adjusted_scores[i] - ((length ** -3) * 100)
        else:
            adjusted_scores[i] = -100
    return adjusted_outputs, adjusted_scores


def sort_outputs(outputs: Sequence[str], scores: Sequence[float]) -> Tuple[List[str], List[float]]:
    ordered = sorted(zip(scores, outputs), reverse=True)
    if not ordered:
        return [], []
    new_scores, new_outputs = zip(*ordered)
    return list(new_outputs), list(new_scores)


def predict_text(
    model,  # repo model instance
    in_str: str,
    *,
    censor_words: Sequence[str] = (),
    max_input_length: int = 50,
):
    """Return ranked outputs and scores for a raw input string."""

    if len(in_str) == 0 or len(in_str) > max_input_length:
        return ["您的输入太长了"], []
    model_outputs, model_scores = model.infer(" ".join(in_str))
    model_scores = list(model_scores.tolist())
    outputs, scores = manual_correct_result(
        in_str,
        model_outputs,
        model_scores,
        censor_words=censor_words,
    )
    return sort_outputs(outputs, scores)


def build_flask_app(
    model,
    *,
    censor_words: Sequence[str] = (),
    max_input_length: int = 50,
    enable_cors: bool = True,
):
    """Create the Flask app used by the bundled inference wrapper."""

    from flask import Flask, jsonify

    if enable_cors:
        from flask_cors import CORS

    app = Flask(__name__)
    if enable_cors:
        CORS(app)

    @app.route("/chat/couplet/<in_str>")
    def chat_couplet(in_str):
        outputs, _ = predict_text(
            model,
            in_str,
            censor_words=censor_words,
            max_input_length=max_input_length,
        )
        return jsonify({"output": outputs[0]})

    @app.route("/v0.2/couplet/<in_str>")
    def chat_couplet_v2(in_str):
        outputs, scores = predict_text(
            model,
            in_str,
            censor_words=censor_words,
            max_input_length=max_input_length,
        )
        return jsonify({"output": outputs, "score": scores})

    return app


def load_inference_model(
    repo_root: Optional[Union[str, Path]],
    *,
    vocab_file: Union[str, Path],
    model_dir: Union[str, Path],
    num_units: int = 1024,
    layers: int = 4,
    dropout: float = 0.2,
):
    """Instantiate the repo's model in inference mode and restore its checkpoint."""

    return build_model(
        repo_root,
        train_input_file=None,
        train_target_file=None,
        test_input_file=None,
        test_target_file=None,
        vocab_file=vocab_file,
        num_units=num_units,
        layers=layers,
        dropout=dropout,
        batch_size=1,
        learning_rate=0.0001,
        output_dir=model_dir,
        restore_model=True,
        init_train=False,
        init_infer=True,
    )


def summarize_fixture(paths: Dict[str, Path]) -> str:
    """Return a compact JSON summary for scripts that want to print their setup."""

    summary = {key: str(value) for key, value in paths.items() if key != "model"}
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2)
