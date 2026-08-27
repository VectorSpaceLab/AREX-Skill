#!/usr/bin/env python3
"""Deterministic smoke helper for cleanlab outlier routing."""

from __future__ import annotations

import json
from typing import Callable

import numpy as np

from cleanlab.outlier import OutOfDistribution
from cleanlab.rank import find_top_issues


def expect_value_error(func: Callable[[], object], expected_fragment: str) -> None:
    try:
        func()
    except ValueError as exc:
        message = str(exc)
        if expected_fragment not in message:
            raise AssertionError(
                f"Expected ValueError containing {expected_fragment!r}, got: {message!r}"
            ) from exc
    else:
        raise AssertionError(f"Expected ValueError containing {expected_fragment!r}")


def feature_case() -> dict:
    features = np.array(
        [
            [0.00, 0.00],
            [0.10, 0.00],
            [0.00, 0.10],
            [0.10, 0.10],
            [4.00, 4.00],
        ],
        dtype=float,
    )

    fitted = OutOfDistribution(params={"k": 2})
    fitted.fit(features=features, verbose=False)
    scores = fitted.score(features=features)
    fit_scores = OutOfDistribution(params={"k": 2}).fit_score(features=features, verbose=False)

    assert scores.shape == (len(features),)
    assert fit_scores.shape == (len(features),)
    assert np.all((0.0 <= scores) & (scores <= 1.0))
    assert np.all((0.0 <= fit_scores) & (fit_scores <= 1.0))
    assert int(np.argmin(scores)) == 4
    assert int(np.argmin(fit_scores)) == 4
    assert find_top_issues(scores, top=1).tolist() == [4]
    assert find_top_issues(fit_scores, top=1).tolist() == [4]

    return {
        "top_index": int(np.argmin(scores)),
        "fit_top_index": int(np.argmin(fit_scores)),
        "scores": [float(value) for value in scores],
    }


def pred_probs_case() -> dict:
    pred_probs = np.array(
        [
            [0.97, 0.02, 0.01],
            [0.02, 0.94, 0.04],
            [0.01, 0.02, 0.97],
            [0.96, 0.02, 0.02],
            [0.34, 0.33, 0.33],
        ],
        dtype=float,
    )
    labels = np.array([0, 1, 2, 0, 1], dtype=int)

    unadjusted = OutOfDistribution(params={"adjust_pred_probs": False})
    unadjusted_scores = unadjusted.score(pred_probs=pred_probs)
    assert unadjusted_scores.shape == (len(pred_probs),)
    assert np.all((0.0 <= unadjusted_scores) & (unadjusted_scores <= 1.0))
    assert int(np.argmin(unadjusted_scores)) == 4
    assert find_top_issues(unadjusted_scores, top=1).tolist() == [4]

    adjusted = OutOfDistribution()
    adjusted.fit(pred_probs=pred_probs, labels=labels, verbose=False)
    adjusted_scores = adjusted.score(pred_probs=pred_probs)
    adjusted_fit_scores = OutOfDistribution().fit_score(
        pred_probs=pred_probs,
        labels=labels,
        verbose=False,
    )

    np.testing.assert_allclose(adjusted_scores, adjusted_fit_scores)
    assert adjusted_scores.shape == (len(pred_probs),)
    assert np.all((0.0 <= adjusted_scores) & (adjusted_scores <= 1.0))
    assert int(np.argmin(adjusted_scores)) == 4

    expect_value_error(
        lambda: OutOfDistribution().fit(pred_probs=pred_probs, verbose=False),
        "Cannot calculate adjust_pred_probs without labels",
    )

    return {
        "unadjusted_top_index": int(np.argmin(unadjusted_scores)),
        "adjusted_top_index": int(np.argmin(adjusted_scores)),
        "unadjusted_scores": [float(value) for value in unadjusted_scores],
    }


def main() -> int:
    results = {
        "features": feature_case(),
        "pred_probs": pred_probs_case(),
    }
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
