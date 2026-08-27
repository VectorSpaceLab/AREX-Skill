#!/usr/bin/env python3
"""Tiny evaluator smoke checks for the OGB-LSC family."""

from __future__ import annotations

import numpy as np
import torch

from ogb.lsc import (
    MAG240MEvaluator,
    PCQM4MEvaluator,
    PCQM4Mv2Evaluator,
    WikiKG90MEvaluator,
    WikiKG90Mv2Evaluator,
)


def main() -> None:
    print("pcqm4m:", PCQM4MEvaluator().eval({"y_true": torch.tensor([1.0, 2.0]), "y_pred": torch.tensor([1.1, 1.9])}))
    print("pcqm4m-v2:", PCQM4Mv2Evaluator().eval({"y_true": np.array([1.0, 2.0]), "y_pred": np.array([1.1, 1.9])}))
    print("mag240m:", MAG240MEvaluator().eval({"y_true": torch.tensor([1, 2]), "y_pred": torch.tensor([1, 1])}))

    wiki90m = WikiKG90MEvaluator().eval(
        {"h,r->t": {"t_pred_top10": torch.tensor([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]), "t_correct_index": torch.tensor([1])}}
    )
    print("wikikg90m:", wiki90m)

    wiki90mv2 = WikiKG90Mv2Evaluator().eval(
        {"h,r->t": {"t_pred_top10": np.array([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]), "t": np.array([1])}}
    )
    print("wikikg90m-v2:", wiki90mv2)


if __name__ == "__main__":
    main()
