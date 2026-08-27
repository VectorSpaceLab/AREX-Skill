#!/usr/bin/env python3
"""Tiny in-memory smoke checks for Flower Datasets."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from datasets import Dataset

import flwr_datasets
from flwr_datasets import FederatedDataset
from flwr_datasets.partitioner import (
    DirichletPartitioner,
    IidPartitioner,
    PathologicalPartitioner,
)
from flwr_datasets.preprocessor import Divider, Merger
from flwr_datasets.visualization import (
    plot_comparison_label_distribution,
    plot_label_distributions,
)


def _build_tiny_dataset() -> Dataset:
    """Build a tiny balanced in-memory dataset."""
    return Dataset.from_dict(
        {
            "x": list(range(6)),
            "label": [0, 0, 0, 1, 1, 1],
        }
    )


def _smoke_iid(dataset: Dataset, num_partitions: int) -> list[int]:
    """Check that IID partitioning works on a tiny in-memory dataset."""
    partitioner = IidPartitioner(num_partitions=num_partitions)
    partitioner.dataset = dataset
    lengths = [len(partitioner.load_partition(pid)) for pid in range(num_partitions)]
    if sum(lengths) != len(dataset):
        raise AssertionError("IID partition lengths do not cover the dataset.")
    if max(lengths) - min(lengths) > 1:
        raise AssertionError("IID partition sizes are not balanced.")
    return lengths


def _smoke_pathological(dataset: Dataset) -> list[list[int]]:
    """Check that a tiny class-constrained partitioner works."""
    partitioner = PathologicalPartitioner(
        num_partitions=2,
        partition_by="label",
        num_classes_per_partition=1,
        class_assignment_mode="deterministic",
    )
    partitioner.dataset = dataset
    partitions = [partitioner.load_partition(pid) for pid in range(2)]
    labels = [sorted(set(partition["label"])) for partition in partitions]
    if labels != [[0], [1]]:
        raise AssertionError(f"Unexpected pathological partition labels: {labels!r}")
    if [len(partition) for partition in partitions] != [3, 3]:
        raise AssertionError("Pathological partition sizes do not match the fixture.")
    return labels


def main(argv: Sequence[str] | None = None) -> int:
    """Run the smoke check."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--partitions", type=int, default=2, help="IID partitions.")
    args = parser.parse_args(argv)

    if args.partitions < 2:
        raise SystemExit("--partitions must be at least 2.")

    dataset = _build_tiny_dataset()
    iid_lengths = _smoke_iid(dataset, args.partitions)
    pathological_labels = _smoke_pathological(dataset)

    # Keep the installed surface in the smoke path so import regressions surface early.
    _ = (
        FederatedDataset,
        DirichletPartitioner,
        Divider,
        Merger,
        plot_label_distributions,
        plot_comparison_label_distribution,
        flwr_datasets.__all__,
    )

    print(
        "ok flwr-datasets",
        flwr_datasets.__version__,
        f"iid={iid_lengths}",
        f"pathological={pathological_labels}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
