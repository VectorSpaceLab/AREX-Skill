#!/usr/bin/env python3
"""Tiny in-memory smoke checks for Snorkel data transforms."""

from __future__ import annotations

import argparse
import json
from types import SimpleNamespace
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from snorkel.augmentation import (
    ApplyAllPolicy,
    ApplyEachPolicy,
    ApplyOnePolicy,
    MeanFieldPolicy,
    PandasTFApplier,
    RandomPolicy,
    TFApplier,
    transformation_function,
)
from snorkel.map import Mapper, lambda_mapper
from snorkel.preprocess import Preprocessor, preprocessor
from snorkel.synthetic.synthetic_data import generate_simple_label_matrix


class AddLengthMapper(Mapper):
    """Map a text field to its character length."""

    def __init__(self) -> None:
        super().__init__("add_length", mapped_field_names=dict(text_len="length"))

    def run(self, text: str) -> Dict[str, int]:
        return dict(text_len=len(text))


class AddTextInfoPreprocessor(Preprocessor):
    """Preprocess text into normalized text and a length field."""

    def __init__(self) -> None:
        super().__init__("add_text_info")

    def run(self, text: str) -> Dict[str, Any]:
        text_norm = text.strip().lower()
        return dict(text_norm=text_norm, text_len=len(text_norm))


def _ensure(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def smoke_mapper_and_preprocessor() -> Dict[str, Any]:
    mapper = AddLengthMapper()
    mapper_input = SimpleNamespace(text="  Hello  ", payload={"values": [1, 2]})
    mapper_output = mapper(mapper_input)
    _ensure(mapper_output is not None, "Mapper returned None")
    _ensure(mapper_input.text == "  Hello  ", "Mapper mutated the source object")
    _ensure(hasattr(mapper_output, "length"), "Mapped field was not renamed")
    _ensure(mapper_output.length == 9, "Unexpected mapped length")

    base_preprocessor = AddTextInfoPreprocessor()
    base_pre_input = SimpleNamespace(text="  Alpha  ")
    base_pre_output = base_preprocessor(base_pre_input)
    _ensure(base_pre_output is not None, "Preprocessor class failed")
    _ensure(base_pre_input.text == "  Alpha  ", "Preprocessor class mutated the source object")
    _ensure(
        base_pre_output.text_norm == "alpha" and base_pre_output.text_len == 5,
        "Unexpected Preprocessor class output",
    )

    lambda_hits = {"count": 0}

    @lambda_mapper(memoize=True)
    def add_square(x: SimpleNamespace) -> SimpleNamespace:
        lambda_hits["count"] += 1
        x.square = x.payload["values"][0] ** 2
        return x

    memo_input = SimpleNamespace(uid="row-1", payload={"values": [1, 2]})
    memo_first = add_square(memo_input)
    memo_second = add_square(memo_input)
    _ensure(memo_first is not None and memo_second is not None, "Lambda mapper failed")
    _ensure(lambda_hits["count"] == 1, "Memoization did not reuse the cached output")
    _ensure(memo_input.payload == {"values": [1, 2]}, "Lambda mapper mutated the source object")

    pre_hits = {"count": 0}

    @preprocessor()
    def strip_text(x: SimpleNamespace) -> SimpleNamespace:
        x.text = x.text.strip()
        return x

    @preprocessor(pre=[strip_text], memoize=True)
    def add_text_len(x: SimpleNamespace) -> SimpleNamespace:
        pre_hits["count"] += 1
        x.text_len = len(x.text)
        return x

    pre_input = SimpleNamespace(text="  Hi  ", payload={"values": [3]})
    pre_first = add_text_len(pre_input)
    pre_second = add_text_len(pre_input)
    _ensure(pre_first is not None and pre_second is not None, "Preprocessor failed")
    _ensure(pre_hits["count"] == 1, "Preprocessor memoization did not cache the result")
    _ensure(pre_input.text == "  Hi  ", "Preprocessor mutated the source object")
    _ensure(pre_first.text == "Hi" and pre_first.text_len == 2, "Unexpected preprocessor output")

    return {
        "base_preprocessor_length": base_pre_output.text_len,
        "lambda_hits": lambda_hits["count"],
        "mapper_length": mapper_output.length,
        "preprocessor_hits": pre_hits["count"],
    }


def smoke_policies_and_augmentation() -> Dict[str, Any]:
    _ensure(
        ApplyOnePolicy(n_per_original=1, keep_original=True).generate_for_example() == [[], [0]],
        "ApplyOnePolicy generated an unexpected sequence",
    )
    _ensure(
        ApplyEachPolicy(2, keep_original=True).generate_for_example() == [[], [0], [1]],
        "ApplyEachPolicy generated an unexpected sequence",
    )
    _ensure(
        ApplyAllPolicy(2, n_per_original=2, keep_original=False).generate_for_example()
        == [[0, 1], [0, 1]],
        "ApplyAllPolicy generated an unexpected sequence",
    )

    np.random.seed(0)
    mean_field = MeanFieldPolicy(2, sequence_length=2, p=[1.0, 0.0])
    _ensure(mean_field.generate() == [0, 0], "MeanFieldPolicy did not follow the supplied distribution")

    np.random.seed(0)
    random_policy = RandomPolicy(2, sequence_length=2)
    random_seq = random_policy.generate()
    _ensure(len(random_seq) == 2, "RandomPolicy returned the wrong sequence length")
    _ensure(all(0 <= idx < 2 for idx in random_seq), "RandomPolicy returned an out-of-range TF index")

    @transformation_function()
    def add_ten_or_drop(x: SimpleNamespace) -> SimpleNamespace | None:
        if x.num == 2:
            return None
        x.num += 10
        return x

    policy = ApplyOnePolicy(n_per_original=1, keep_original=True)
    records = [SimpleNamespace(num=1), SimpleNamespace(num=2)]
    list_augmented = TFApplier([add_ten_or_drop], policy).apply(records, progress_bar=False)
    _ensure([item.num for item in list_augmented] == [1, 11, 2], "Unexpected list augmentation output")
    _ensure([item.num for item in records] == [1, 2], "TFApplier mutated the input list")

    frame = pd.DataFrame({"num": [1, 2]})
    frame_augmented = PandasTFApplier([add_ten_or_drop], policy).apply(frame, progress_bar=False)
    expected = pd.DataFrame({"num": [1, 11, 2]}, index=[0, 0, 1])
    assert_frame_equal(frame_augmented, expected)
    assert_frame_equal(frame, pd.DataFrame({"num": [1, 2]}))

    return {
        "random_policy_seq": random_seq,
        "augmented_rows": len(frame_augmented),
    }


def smoke_synthetic() -> Dict[str, Any]:
    np.random.seed(7)
    P, Y, L = generate_simple_label_matrix(n=5, m=3, cardinality=2, abstain_multiplier=1.25)
    _ensure(P.shape == (3, 3, 2), "Unexpected P shape")
    _ensure(Y.shape == (5,), "Unexpected Y shape")
    _ensure(L.shape == (5, 3), "Unexpected L shape")
    np.testing.assert_allclose(P.sum(axis=1), np.ones((3, 2)))
    _ensure(set(np.unique(Y)).issubset({0, 1}), "Y contains out-of-range labels")
    _ensure(set(np.unique(L)).issubset({-1, 0, 1}), "L contains out-of-range labels")
    return {
        "P_shape": list(P.shape),
        "Y_shape": list(Y.shape),
        "L_shape": list(L.shape),
    }


def smoke_spacy() -> Dict[str, Any]:
    try:
        from snorkel.preprocess.nlp import SpacyPreprocessor
    except Exception as exc:  # pragma: no cover - optional dependency guard
        return {"status": "skipped", "reason": f"spaCy unavailable: {exc}"}

    try:
        spacy_pre = SpacyPreprocessor("text", "doc", memoize=True)
    except Exception as exc:  # pragma: no cover - optional dependency guard
        return {"status": "skipped", "reason": f"spaCy model unavailable: {exc}"}

    sample = SimpleNamespace(text="Jane plays soccer.")
    output_1 = spacy_pre(sample)
    output_2 = spacy_pre(sample)
    _ensure(output_1 is not None and output_2 is not None, "SpacyPreprocessor failed")
    _ensure(sample.text == "Jane plays soccer.", "SpacyPreprocessor mutated the source object")
    _ensure(len(output_1.doc) > 0, "SpacyPreprocessor produced an empty doc")
    _ensure(output_1.doc[0].text == "Jane", "Unexpected spaCy tokenization")
    return {
        "status": "ok",
        "tokens": len(output_1.doc),
        "repeat_tokens": len(output_2.doc),
    }


def smoke_spark() -> Dict[str, Any]:
    try:
        from pyspark.sql import Row
    except Exception as exc:  # pragma: no cover - optional dependency guard
        return {"status": "skipped", "reason": f"PySpark unavailable: {exc}"}

    from snorkel.map.spark import make_spark_mapper
    from snorkel.preprocess.spark import make_spark_preprocessor

    class SparkLengthMapper(Mapper):
        def run(self, text: str) -> Dict[str, int]:
            return dict(text_len=len(text))

    class SparkTextPreprocessor(Preprocessor):
        def run(self, text: str) -> Dict[str, Any]:
            text_norm = text.strip().lower()
            return dict(text_norm=text_norm, text_len=len(text_norm))

    spark_mapper = make_spark_mapper(SparkLengthMapper("spark_length"))
    mapped_row = spark_mapper(Row(text="abc"))
    _ensure(mapped_row is not None, "Spark mapper returned None")
    _ensure(mapped_row.text_len == 3, "Spark mapper produced the wrong length")
    _ensure(mapped_row.text == "abc", "Spark mapper changed the source field")

    spark_pre = make_spark_preprocessor(SparkTextPreprocessor("spark_text_pre"))
    preprocessed_row = spark_pre(Row(text="  AbC  "))
    _ensure(preprocessed_row is not None, "Spark preprocessor returned None")
    _ensure(preprocessed_row.text_norm == "abc", "Spark preprocessor normalized the text incorrectly")
    _ensure(preprocessed_row.text_len == 3, "Spark preprocessor produced the wrong length")

    return {
        "status": "ok",
        "mapper_length": mapped_row.text_len,
        "pre_length": preprocessed_row.text_len,
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tiny smoke checks for Snorkel data transforms.")
    parser.parse_args(argv)

    summary = {
        "mapper_and_preprocessor": smoke_mapper_and_preprocessor(),
        "policies_and_augmentation": smoke_policies_and_augmentation(),
        "synthetic": smoke_synthetic(),
        "spacy": smoke_spacy(),
        "spark": smoke_spark(),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main())
