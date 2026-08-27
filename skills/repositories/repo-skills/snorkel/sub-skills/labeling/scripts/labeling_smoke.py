#!/usr/bin/env python3
"""Tiny in-memory smoke for Snorkel labeling.

This script exercises LF authoring, Pandas application, LFAnalysis, and a tiny
LabelModel fit when the core dependencies are available.
"""

from __future__ import annotations

import warnings
from typing import Any


def _add_len(x: Any) -> Any:
    x["n_tokens"] = len(str(x["text"]).split())
    return x


def _has_cat(x: Any, keyword: str) -> int:
    return 1 if keyword in str(x["text"]).lower() else -1


def _is_short(x: Any) -> int:
    return 0 if x["n_tokens"] <= 1 else -1


def _mentions_dog(x: Any) -> int:
    return 1 if "dog" in str(x["text"]).lower() else -1


def main() -> int:
    try:
        import numpy as np
        import pandas as pd
        from snorkel.labeling import LFAnalysis, PandasLFApplier, filter_unlabeled_dataframe, labeling_function
        from snorkel.labeling.model import LabelModel, MajorityLabelVoter
        from snorkel.preprocess import preprocessor
    except Exception as exc:  # pragma: no cover - dependency gate
        print(f"SKIP: core labeling smoke not run ({exc}).")
        return 0

    warnings.filterwarnings("ignore", category=FutureWarning)

    add_len = preprocessor()(_add_len)
    has_cat = labeling_function(resources={"keyword": "cat"})(_has_cat)
    is_short = labeling_function(pre=[add_len])(_is_short)
    mentions_dog = labeling_function()(_mentions_dog)

    df = pd.DataFrame(
        {
            "text": ["cat", "small dog", "other", "cat dog", "plain words"],
        }
    )

    applier = PandasLFApplier([has_cat, is_short, mentions_dog])
    L, meta = applier.apply(df, progress_bar=False, fault_tolerant=True, return_meta=True)
    expected = np.array(
        [
            [1, 0, -1],
            [-1, -1, 1],
            [-1, 0, -1],
            [1, -1, 1],
            [-1, -1, -1],
        ]
    )
    np.testing.assert_array_equal(L, expected)

    print("L shape:", L.shape)
    print("faults:", dict(meta.faults))

    analysis = LFAnalysis(L, [has_cat, is_short, mentions_dog])
    print("coverage:", round(analysis.label_coverage(), 3))
    print("overlap:", round(analysis.label_overlap(), 3))
    print("conflict:", round(analysis.label_conflict(), 3))
    print("summary columns:", list(analysis.lf_summary().columns))

    label_model = LabelModel(cardinality=2, verbose=False)
    mode = "labelmodel"
    try:
        label_model.fit(L, n_epochs=25, lr=0.01, seed=123, progress_bar=False)
        probs = label_model.predict_proba(L)
        preds = label_model.predict(L)
    except Exception as exc:  # pragma: no cover - fallback path
        mode = f"voter:{type(exc).__name__}"
        print(f"LabelModel fallback: {exc}")
        voter = MajorityLabelVoter()
        probs = voter.predict_proba(L)
        preds = probs.argmax(axis=1)

    print("mode:", mode)
    print("probs shape:", probs.shape)
    print("preds:", preds.tolist())

    X_train, probs_train = filter_unlabeled_dataframe(df, probs, L)
    print("filtered rows:", len(X_train))
    print("filtered probs shape:", probs_train.shape)

    assert probs.shape == (5, 2)
    assert preds.shape == (5,)
    assert len(X_train) == 4
    assert probs_train.shape == (4, 2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
