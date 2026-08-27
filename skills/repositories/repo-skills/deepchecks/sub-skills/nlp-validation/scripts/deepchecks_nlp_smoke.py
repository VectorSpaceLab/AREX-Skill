#!/usr/bin/env python3
"""Safe Deepchecks NLP smoke helper.

Builds tiny local TextData examples for text classification, token
classification, or multilabel classification, attaches precomputed metadata,
properties, and embeddings, and optionally runs one of the built-in NLP suites.
The script performs no network calls by default, uses no external files, and
writes no reports unless future options are added.
"""
from __future__ import annotations

import argparse
import json
import os
import warnings
from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class SmokeCase:
    """One tiny offline NLP validation scenario."""

    scenario: str
    train: Any
    test: Any
    train_predictions: Any
    test_predictions: Any
    train_probabilities: Any
    test_probabilities: Any
    model_classes: Optional[List[Any]]
    tokenizer: Any = None


class TinyWhitespaceTokenizer:
    """Minimal Hugging Face-like tokenizer stub for offline smoke runs."""

    def __init__(self, texts):
        self.unk_token_id = 1
        self.is_fast = True
        self.model_max_length = 10**9
        self.special_tokens_map = {
            "cls_token": "[CLS]",
            "sep_token": "[SEP]",
            "pad_token": "[PAD]",
            "unk_token": "[UNK]",
        }
        self._vocab = {"[PAD]": 0, "[UNK]": 1, "[CLS]": 101, "[SEP]": 102}
        for text in texts:
            for token in text.split():
                self._vocab.setdefault(token, len(self._vocab) + 1)

    def tokenize(self, text):
        return text.split()

    def convert_tokens_to_ids(self, token):
        return self._vocab.get(token, self.unk_token_id)

    def __call__(self, texts, **kwargs):
        input_ids = []
        offset_mapping = []
        for text in texts:
            ids = [self.convert_tokens_to_ids("[CLS]")]
            spans = [(0, 0)]
            cursor = 0
            for token in text.split():
                start = text.find(token, cursor)
                if start < 0:
                    start = text.find(token)
                end = start + len(token)
                cursor = end + 1
                ids.append(self.convert_tokens_to_ids(token))
                spans.append((start, end))
            ids.append(self.convert_tokens_to_ids("[SEP]"))
            spans.append((0, 0))
            input_ids.append(ids)
            offset_mapping.append(spans)
        return {"input_ids": input_ids, "offset_mapping": offset_mapping}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a safe tiny Deepchecks NLP smoke test.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--scenario",
        choices=("text-classification", "token-classification", "multilabel"),
        default="text-classification",
        help="Which tiny local TextData setup to build.",
    )
    parser.add_argument(
        "--suite",
        choices=("data-integrity", "train-test-validation", "model-evaluation", "full-suite"),
        default="data-integrity",
        help="Which built-in NLP suite to run after construction.",
    )
    parser.add_argument(
        "--skip-run",
        action="store_true",
        help="Only verify imports and construct the tiny data objects.",
    )
    return parser.parse_args()


def _safe_imports():
    try:
        from deepchecks.nlp import TextData
        from deepchecks.nlp.suites import data_integrity, full_suite, model_evaluation, train_test_validation
    except ImportError as exc:  # pragma: no cover - depends on local environment
        raise SystemExit(
            "deepchecks.nlp imports failed. Install deepchecks[nlp] and, when you need built-in properties, "
            "deepchecks[nlp-properties]."
        ) from exc
    return TextData, data_integrity, train_test_validation, model_evaluation, full_suite


def _build_tables(texts):
    import numpy as np
    import pandas as pd

    lengths = [len(text) for text in texts]
    word_counts = [len(text.split()) for text in texts]
    char_sums = [sum(ord(ch) for ch in text) for text in texts]

    metadata = pd.DataFrame(
        {
            "source": ["web" if i % 2 == 0 else "app" for i in range(len(texts))],
            "segment": [f"seg-{i % 3}" for i in range(len(texts))],
            "rank": list(range(len(texts))),
        }
    )

    properties = pd.DataFrame(
        {
            "Text Length": lengths,
            "Average Word Length": [round(sum(len(word) for word in text.split()) / len(text.split()), 2) for text in texts],
            "Language": ["en"] * len(texts),
            "tone_bucket": ["short" if length < 35 else "long" for length in lengths],
            "token_count": word_counts,
        }
    )

    embeddings = np.column_stack(
        [
            np.asarray(lengths, dtype=float),
            np.asarray(word_counts, dtype=float),
            np.asarray(char_sums, dtype=float),
            np.asarray([i % 4 for i in range(len(texts))], dtype=float),
        ]
    )

    return metadata, properties, embeddings


def _flip_binary_label(label: str) -> str:
    return "negative" if label == "positive" else "positive"


def build_text_case(TextData) -> SmokeCase:
    train_texts = [
        f"train positive sample {i} bright wording smooth checkout" if i % 2 == 0
        else f"train negative sample {i} rough wording slow support"
        for i in range(12)
    ]
    test_texts = [
        f"test positive sample {i} easy use quick delivery" if i % 2 == 0
        else f"test negative sample {i} delayed reply weak packaging"
        for i in range(12)
    ]
    train_labels = ["positive" if i % 2 == 0 else "negative" for i in range(12)]
    test_labels = ["positive" if i % 2 == 0 else "negative" for i in range(12)]

    train_metadata, train_properties, train_embeddings = _build_tables(train_texts)
    test_metadata, test_properties, test_embeddings = _build_tables(test_texts)

    train = TextData(
        raw_text=train_texts,
        label=train_labels,
        task_type="text_classification",
        metadata=train_metadata,
        categorical_metadata=["source", "segment"],
        properties=train_properties,
        categorical_properties=["tone_bucket"],
        embeddings=train_embeddings,
        name="Train",
    )
    test = TextData(
        raw_text=test_texts,
        label=test_labels,
        task_type="text_classification",
        metadata=test_metadata,
        categorical_metadata=["source", "segment"],
        properties=test_properties,
        categorical_properties=["tone_bucket"],
        embeddings=test_embeddings,
        name="Test",
    )

    train_predictions = list(train_labels)
    test_predictions = list(test_labels)
    train_predictions[3] = _flip_binary_label(train_predictions[3])
    test_predictions[8] = _flip_binary_label(test_predictions[8])

    train_probabilities = [
        [0.86, 0.14] if prediction == "negative" else [0.12, 0.88]
        for prediction in train_predictions
    ]
    test_probabilities = [
        [0.84, 0.16] if prediction == "negative" else [0.18, 0.82]
        for prediction in test_predictions
    ]

    tokenizer = TinyWhitespaceTokenizer(train_texts + test_texts)
    return SmokeCase(
        scenario="text-classification",
        train=train,
        test=test,
        train_predictions=train_predictions,
        test_predictions=test_predictions,
        train_probabilities=train_probabilities,
        test_probabilities=test_probabilities,
        model_classes=["negative", "positive"],
        tokenizer=tokenizer,
    )


def build_token_case(TextData) -> SmokeCase:
    train_tokens = [[f"Dan{i}", "lives", "in", "New", "York"] for i in range(12)]
    test_tokens = [[f"Mia{i}", "works", "at", "Google"] for i in range(12)]
    train_labels = [["B-PER", "O", "O", "B-LOC", "I-LOC"] for _ in range(12)]
    test_labels = [["B-PER", "O", "O", "B-ORG"] for _ in range(12)]

    train_texts = [" ".join(tokens) for tokens in train_tokens]
    test_texts = [" ".join(tokens) for tokens in test_tokens]
    train_metadata, train_properties, train_embeddings = _build_tables(train_texts)
    test_metadata, test_properties, test_embeddings = _build_tables(test_texts)

    train = TextData(
        raw_text=train_texts,
        tokenized_text=train_tokens,
        label=train_labels,
        task_type="token_classification",
        metadata=train_metadata,
        categorical_metadata=["source", "segment"],
        properties=train_properties,
        categorical_properties=["tone_bucket"],
        embeddings=train_embeddings,
        name="Train",
    )
    test = TextData(
        raw_text=test_texts,
        tokenized_text=test_tokens,
        label=test_labels,
        task_type="token_classification",
        metadata=test_metadata,
        categorical_metadata=["source", "segment"],
        properties=test_properties,
        categorical_properties=["tone_bucket"],
        embeddings=test_embeddings,
        name="Test",
    )

    train_predictions = [list(row) for row in train_labels]
    test_predictions = [list(row) for row in test_labels]
    train_predictions[1] = ["B-PER", "O", "O", "B-ORG", "I-LOC"]
    test_predictions[2] = ["B-PER", "O", "B-ORG", "B-ORG"]

    tokenizer = TinyWhitespaceTokenizer(train_texts + test_texts)
    return SmokeCase(
        scenario="token-classification",
        train=train,
        test=test,
        train_predictions=train_predictions,
        test_predictions=test_predictions,
        train_probabilities=None,
        test_probabilities=None,
        model_classes=["B-LOC", "B-ORG", "B-PER"],
        tokenizer=tokenizer,
    )


def build_multilabel_case(TextData) -> SmokeCase:
    import numpy as np

    train_texts = [
        f"train multilabel item {i} clean useful content" if i % 2 == 0
        else f"train multilabel item {i} noisy mixed content"
        for i in range(12)
    ]
    test_texts = [
        f"test multilabel item {i} clean useful content" if i % 2 == 0
        else f"test multilabel item {i} noisy mixed content"
        for i in range(12)
    ]
    train_labels = np.array(
        [
            [1, 0, 1],
            [1, 1, 0],
            [0, 1, 1],
            [1, 0, 0],
            [1, 1, 1],
            [0, 1, 0],
            [1, 0, 1],
            [1, 1, 0],
            [0, 1, 1],
            [1, 0, 0],
            [1, 1, 1],
            [0, 1, 0],
        ],
        dtype=int,
    )
    test_labels = np.array(
        [
            [1, 0, 0],
            [0, 1, 1],
            [1, 1, 0],
            [1, 0, 1],
            [0, 1, 0],
            [1, 1, 1],
            [1, 0, 0],
            [0, 1, 1],
            [1, 1, 0],
            [1, 0, 1],
            [0, 1, 0],
            [1, 1, 1],
        ],
        dtype=int,
    )

    train_metadata, train_properties, train_embeddings = _build_tables(train_texts)
    test_metadata, test_properties, test_embeddings = _build_tables(test_texts)

    train = TextData(
        raw_text=train_texts,
        label=train_labels.tolist(),
        task_type="text_classification",
        metadata=train_metadata,
        categorical_metadata=["source", "segment"],
        properties=train_properties,
        categorical_properties=["tone_bucket"],
        embeddings=train_embeddings,
        name="Train",
    )
    test = TextData(
        raw_text=test_texts,
        label=test_labels.tolist(),
        task_type="text_classification",
        metadata=test_metadata,
        categorical_metadata=["source", "segment"],
        properties=test_properties,
        categorical_properties=["tone_bucket"],
        embeddings=test_embeddings,
        name="Test",
    )

    train_predictions = train_labels.copy()
    test_predictions = test_labels.copy()
    train_predictions[2, 1] = 0
    test_predictions[5, 0] = 0

    train_probabilities = np.clip(train_predictions * 0.8 + 0.1, 0, 1)
    test_probabilities = np.clip(test_predictions * 0.8 + 0.1, 0, 1)

    tokenizer = TinyWhitespaceTokenizer(train_texts + test_texts)
    return SmokeCase(
        scenario="multilabel",
        train=train,
        test=test,
        train_predictions=train_predictions.tolist(),
        test_predictions=test_predictions.tolist(),
        train_probabilities=train_probabilities.tolist(),
        test_probabilities=test_probabilities.tolist(),
        model_classes=["bug", "feature", "quality"],
        tokenizer=tokenizer,
    )


def build_case(TextData, scenario: str) -> SmokeCase:
    if scenario == "text-classification":
        return build_text_case(TextData)
    if scenario == "token-classification":
        return build_token_case(TextData)
    if scenario == "multilabel":
        return build_multilabel_case(TextData)
    raise ValueError(f"Unsupported scenario: {scenario}")


def build_suite(suite_name: str, factories, case: SmokeCase):
    data_integrity, train_test_validation, model_evaluation, full_suite = factories
    common_kwargs = {"n_samples": case.train.n_samples, "random_state": 42}

    if suite_name == "data-integrity":
        kwargs = dict(common_kwargs)
        kwargs["tokenizer"] = case.tokenizer
        return data_integrity(**kwargs)
    if suite_name == "train-test-validation":
        return train_test_validation(**common_kwargs)
    if suite_name == "model-evaluation":
        return model_evaluation(**common_kwargs)
    if suite_name == "full-suite":
        kwargs = dict(common_kwargs)
        kwargs["tokenizer"] = case.tokenizer
        return full_suite(**kwargs)
    raise ValueError(f"Unsupported suite: {suite_name}")


def summarize_case(case: SmokeCase) -> str:
    train = case.train
    test = case.test
    task_type = getattr(train.task_type, "value", str(train.task_type))
    return json.dumps(
        {
            "scenario": case.scenario,
            "train_rows": train.n_samples,
            "test_rows": test.n_samples,
            "task_type": task_type,
            "multilabel": train.is_multi_label_classification(),
            "has_tokenized_text": getattr(train, "_tokenized_text", None) is not None,
            "has_metadata": getattr(train, "_metadata", None) is not None,
            "has_properties": getattr(train, "_properties", None) is not None,
            "has_embeddings": getattr(train, "_embeddings", None) is not None,
            "model_classes": case.model_classes,
            "train_prediction_sample": case.train_predictions[:2],
            "test_prediction_sample": case.test_predictions[:2],
        },
        indent=2,
        default=str,
    )


def summarize_suite_result(result: Any) -> str:
    summary = {
        "result_type": type(result).__name__,
    }
    if hasattr(result, "results"):
        summary["results"] = len(result.results)
    if hasattr(result, "passed"):
        try:
            summary["passed"] = result.passed(fail_if_warning=True, fail_if_check_not_run=False)
        except TypeError:
            summary["passed"] = result.passed()
    if hasattr(result, "get_not_ran_checks"):
        summary["not_ran"] = [check.get_header() for check in result.get_not_ran_checks()]
    if hasattr(result, "get_not_passed_checks"):
        try:
            summary["not_passed"] = [check.get_header() for check in result.get_not_passed_checks(fail_if_warning=True)]
        except TypeError:
            summary["not_passed"] = [check.get_header() for check in result.get_not_passed_checks()]
    return json.dumps(summary, indent=2, default=str)


def main() -> int:
    os.environ.setdefault("DISABLE_LATEST_VERSION_CHECK", "True")
    warnings.filterwarnings(
        "ignore",
        message="pkg_resources is deprecated as an API.*",
        category=UserWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message="ChainedAssignmentError: behaviour will change in pandas 3.0!.*",
        category=FutureWarning,
    )

    args = parse_args()
    TextData, data_integrity, train_test_validation, model_evaluation, full_suite = _safe_imports()
    case = build_case(TextData, args.scenario)

    print(summarize_case(case))

    if args.skip_run:
        print("skip-run requested: imports and TextData construction succeeded")
        return 0

    suite = build_suite(
        args.suite,
        (data_integrity, train_test_validation, model_evaluation, full_suite),
        case,
    )

    run_kwargs = {"with_display": False}
    if case.model_classes is not None:
        run_kwargs["model_classes"] = case.model_classes

    if args.suite in {"data-integrity", "train-test-validation", "model-evaluation", "full-suite"}:
        run_kwargs.update(
            {
                "train_dataset": case.train,
                "test_dataset": case.test,
            }
        )
    else:
        run_kwargs.update({"train_dataset": case.train})

    if args.suite in {"model-evaluation", "full-suite"}:
        run_kwargs.update(
            {
                "train_predictions": case.train_predictions,
                "test_predictions": case.test_predictions,
            }
        )
        if case.train_probabilities is not None:
            run_kwargs["train_probabilities"] = case.train_probabilities
        if case.test_probabilities is not None:
            run_kwargs["test_probabilities"] = case.test_probabilities

    result = suite.run(**run_kwargs)
    print(summarize_suite_result(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
