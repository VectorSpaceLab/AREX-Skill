#!/usr/bin/env python3
"""Tiny CPU-only smoke for snorkel.slicing.

This script stays in memory, uses no external data, and exercises:
- slicing_function + SFApplier
- PandasSFApplier + slice_dataframe
- SliceAwareClassifier.make_slice_dataloader + add_slice_labels
"""

from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import torch
import torch.nn as nn

from snorkel.classification import DictDataset
from snorkel.slicing import (
    PandasSFApplier,
    SFApplier,
    SliceAwareClassifier,
    slice_dataframe,
    slicing_function,
)


@slicing_function()
def is_even(x) -> int:
    return int(x.num % 2 == 0)


@slicing_function()
def is_large(x) -> int:
    return int(x.num >= 2)


def build_rows() -> tuple[list[SimpleNamespace], pd.DataFrame]:
    nums = [0, 1, 2, 3]
    rows = [SimpleNamespace(num=n, text=f"row-{n}") for n in nums]
    df = pd.DataFrame({"num": nums, "text": [f"row-{n}" for n in nums]})
    return rows, df


def main() -> None:
    rows, df = build_rows()
    sf_list = [is_even, is_large]

    rec_from_list = SFApplier(sf_list).apply(rows, progress_bar=False)
    rec_from_df = PandasSFApplier(sf_list).apply(df, progress_bar=False)
    subset = slice_dataframe(df, is_large)

    X = torch.tensor([[float(n), float(n + 1)] for n in range(len(rows))], dtype=torch.float32)
    Y = torch.tensor([0, 1, 0, 1], dtype=torch.long)
    dataset = DictDataset.from_tensors(
        X,
        Y,
        split="train",
        input_data_key="input_data",
        task_name="task",
        dataset_name="slicing-smoke",
    )

    model = SliceAwareClassifier(
        base_architecture=nn.Sequential(
            nn.Linear(2, 4),
            nn.ReLU(),
            nn.Linear(4, 4),
        ),
        head_dim=4,
        slice_names=[sf.name for sf in sf_list],
        input_data_key="input_data",
        task_name="task",
    )
    dl = model.make_slice_dataloader(dataset=dataset, S=rec_from_df, batch_size=2)

    pred_labels = dl.dataset.Y_dict["task_slice:is_large_pred"].tolist()

    print("SFApplier fields:", rec_from_list.dtype.names)
    print("PandasSFApplier fields:", rec_from_df.dtype.names)
    print("slice_dataframe rows:", len(subset))
    print("slice-aware labels:", sorted(dl.dataset.Y_dict))
    print("masked pred labels:", pred_labels)

    assert rec_from_list.dtype.names == rec_from_df.dtype.names
    assert len(subset) == 2
    assert "task_slice:is_large_pred" in dl.dataset.Y_dict
    assert pred_labels == [-1, -1, 0, 1]

    print("slicing smoke OK")


if __name__ == "__main__":
    main()
