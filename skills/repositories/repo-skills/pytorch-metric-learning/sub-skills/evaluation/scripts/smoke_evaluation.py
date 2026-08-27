#!/usr/bin/env python3
"""Tiny evaluation and inference smoke check for PyTorch Metric Learning."""

from __future__ import annotations

import tempfile
from pathlib import Path

import torch

from pytorch_metric_learning.testers import (
    GlobalEmbeddingSpaceTester,
    GlobalTwoStreamEmbeddingSpaceTester,
    WithSameParentLabelTester,
)
from pytorch_metric_learning.utils.accuracy_calculator import AccuracyCalculator
from pytorch_metric_learning.utils.common_functions import EmbeddingDataset
from pytorch_metric_learning.utils.inference import InferenceModel


def build_dataset():
    emb = torch.tensor(
        [[1.0, 0.0], [0.9, 0.1], [-1.0, 0.0], [-0.9, -0.1]], dtype=torch.float32
    )
    labels = torch.tensor([0, 0, 1, 1])
    return EmbeddingDataset(emb, labels)


class TwoStreamDataset(torch.utils.data.Dataset):
    def __init__(self):
        self.anchor = torch.tensor(
            [[1.0, 0.0], [0.9, 0.1], [-1.0, 0.0], [-0.9, -0.1]], dtype=torch.float32
        )
        self.positive = torch.tensor(
            [[0.95, 0.05], [0.85, 0.15], [-0.95, -0.05], [-0.85, -0.15]],
            dtype=torch.float32,
        )
        self.labels = torch.tensor([0, 0, 1, 1])

    def __len__(self):
        return len(self.anchor)

    def __getitem__(self, idx):
        return self.anchor[idx], self.positive[idx], self.labels[idx]


def main() -> None:
    dataset = build_dataset()
    ac = AccuracyCalculator(include=("precision_at_1",), k=1)

    tester = GlobalEmbeddingSpaceTester(
        accuracy_calculator=ac,
        batch_size=2,
        dataloader_num_workers=0,
    )
    out = tester.test({"train": dataset, "val": dataset}, 0, torch.nn.Identity())
    assert "train" in out and "val" in out

    hierarchical = EmbeddingDataset(
        torch.tensor(
            [[1.0, 0.0], [0.9, 0.1], [-1.0, 0.0], [-0.9, -0.1]], dtype=torch.float32
        ),
        torch.tensor([[0, 10], [0, 10], [1, 20], [1, 20]]),
    )
    parent_tester = WithSameParentLabelTester(accuracy_calculator=ac, batch_size=2, dataloader_num_workers=0)
    parent_out = parent_tester.test({"train": hierarchical}, 0, torch.nn.Identity())
    assert "train" in parent_out

    two_stream = TwoStreamDataset()
    two_stream_tester = GlobalTwoStreamEmbeddingSpaceTester(accuracy_calculator=ac, dataloader_num_workers=0)
    two_stream_out = two_stream_tester.test({"train": two_stream}, 0, torch.nn.Identity())
    assert "train" in two_stream_out

    inf = InferenceModel(trunk=torch.nn.Identity(), data_device=torch.device("cpu"))
    with tempfile.TemporaryDirectory(prefix="pml-eval-smoke-") as tmpdir:
        index_file = Path(tmpdir) / "knn.index"
        inf.train_knn(dataset, batch_size=2)
        inf.save_knn_func(str(index_file))
        inf.load_knn_func(str(index_file))
        d, i = inf.get_nearest_neighbors(dataset.embeddings[:1], k=1)
        assert d.shape == i.shape == (1, 1)

    print("evaluation-smoke-ok")


if __name__ == "__main__":
    main()
