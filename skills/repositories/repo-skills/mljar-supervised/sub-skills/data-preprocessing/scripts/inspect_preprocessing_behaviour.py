#!/usr/bin/env python3
"""Inspect small MLJAR preprocessing behaviours with safe in-memory fixtures.

This helper exercises lightweight preprocessing utilities and data assumptions.
It does not train AutoML, read source-repository files, fetch data, or mutate
external state. Run it in an environment where `mljar-supervised` is installed.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Iterable


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run tiny checks for supervised preprocessing utilities and input-shape assumptions."
    )
    parser.add_argument(
        "--skip-text",
        action="store_true",
        help="Skip the tiny TF-IDF text transformer check if sklearn text dependencies are unavailable.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit compact JSON only.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def run_checks(skip_text: bool = False) -> dict[str, Any]:
    import numpy as np
    import pandas as pd
    from supervised.preprocessing.datetime_transformer import DateTimeTransformer
    from supervised.preprocessing.label_encoder import LabelEncoder
    from supervised.preprocessing.preprocessing_missing import PreprocessingMissingValues
    from supervised.preprocessing.preprocessing_utils import PreprocessingUtils

    signals: dict[str, Any] = {"status": "passed"}

    df = pd.DataFrame(
        {
            "num": [1.0, None, 3.5, 4.0],
            "cat": pd.Series(["red", "blue", None, "red"], dtype="category"),
            "dt": pd.to_datetime(["2024-01-01", "2024-01-03", "2024-02-01", "2024-02-03"]),
            "short_text": ["alpha signal", "beta signal", "alpha beta", None],
        }
    )

    type_checks = {col: PreprocessingUtils.get_type(df[col]) for col in ["num", "cat", "dt", "short_text"]}
    signals["type_checks"] = type_checks
    if type_checks["num"] not in {PreprocessingUtils.CONTINOUS, PreprocessingUtils.DISCRETE}:
        raise AssertionError(f"unexpected numeric type: {type_checks['num']}")
    if type_checks["cat"] != PreprocessingUtils.CATEGORICAL:
        raise AssertionError(f"unexpected categorical type: {type_checks['cat']}")
    if type_checks["dt"] != PreprocessingUtils.DATETIME:
        raise AssertionError(f"unexpected datetime type: {type_checks['dt']}")

    missing = PreprocessingMissingValues(columns=["num", "cat", "short_text"])
    filled = df.copy()
    missing.fit(filled)
    filled = missing.transform(filled)
    signals["missing_json_keys"] = sorted(missing.to_json().keys())
    signals["missing_remaining"] = int(filled[["num", "cat", "short_text"]].isna().sum().sum())
    if signals["missing_remaining"] != 0:
        raise AssertionError("missing-value transformer left NA values in selected columns")

    dt = DateTimeTransformer()
    dt_df = df[["dt"]].copy()
    dt.fit(dt_df, "dt")
    dt_out = dt.transform(dt_df)
    signals["datetime_columns"] = list(dt_out.columns)
    if not signals["datetime_columns"]:
        raise AssertionError("datetime transformer did not create derived columns")

    encoder = LabelEncoder()
    encoder.fit(np.array(["small", "medium", "large"]))
    encoded = encoder.transform(np.array(["small", "new_category"]))
    signals["label_encoder_classes_after_new_value"] = list(map(str, encoder.lbl.classes_))
    signals["label_encoder_encoded_len"] = int(len(encoded))
    if "new_category" not in signals["label_encoder_classes_after_new_value"]:
        raise AssertionError("label encoder did not extend classes for a new value")

    if not skip_text:
        from supervised.preprocessing.text_transformer import TextTransformer

        text_df = pd.DataFrame({"text": ["alpha useful signal", "beta useful signal", "alpha beta", "gamma signal"]})
        tt = TextTransformer()
        tt.fit(text_df, "text")
        text_out = tt.transform(text_df)
        signals["text_columns"] = list(text_out.columns)[:10]
        if not signals["text_columns"]:
            raise AssertionError("text transformer produced no TF-IDF columns")
    else:
        signals["text_columns"] = "skipped"

    # Shape-alignment reminders useful before AutoML.fit().
    x = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    y = pd.Series([0, 1, 0], name="target")
    sample_weight = pd.Series([1.0, 0.5, 1.0])
    signals["fit_shape_contract"] = {
        "x_rows": int(x.shape[0]),
        "y_rows": int(y.shape[0]),
        "sample_weight_rows": int(sample_weight.shape[0]),
        "aligned": bool(len(x) == len(y) == len(sample_weight)),
    }
    if not signals["fit_shape_contract"]["aligned"]:
        raise AssertionError("fixture alignment failed")

    return signals


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        signals = run_checks(skip_text=args.skip_text)
        if args.json:
            print(json.dumps(signals, sort_keys=True))
        else:
            print(json.dumps(signals, indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # pragma: no cover - user-facing diagnostics
        print(json.dumps({"status": "failed", "error": type(exc).__name__, "message": str(exc)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
