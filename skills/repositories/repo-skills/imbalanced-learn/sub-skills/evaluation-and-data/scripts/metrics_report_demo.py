#!/usr/bin/env python3
"""Tiny metric-report demo for imbalanced-learn."""

from __future__ import annotations

import numpy as np

from imblearn.metrics import (
    classification_report_imbalanced,
    geometric_mean_score,
    macro_averaged_mean_absolute_error,
    sensitivity_score,
    specificity_score,
)


def main() -> int:
    y_true = np.array([0, 0, 0, 1, 1, 1])
    y_pred = np.array([0, 0, 1, 1, 0, 1])
    print("gmean", round(geometric_mean_score(y_true, y_pred), 3))
    print("sensitivity", round(sensitivity_score(y_true, y_pred), 3))
    print("specificity", round(specificity_score(y_true, y_pred), 3))
    print("report\n" + classification_report_imbalanced(y_true, y_pred))

    y_ord_true = np.array([0, 1, 2, 0, 1, 2])
    y_ord_pred = np.array([0, 2, 2, 0, 1, 1])
    print(
        "ma-mae",
        round(macro_averaged_mean_absolute_error(y_ord_true, y_ord_pred), 3),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
