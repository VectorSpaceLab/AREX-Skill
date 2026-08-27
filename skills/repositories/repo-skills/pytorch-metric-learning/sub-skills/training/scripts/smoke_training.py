#!/usr/bin/env python3
"""Tiny training smoke check for PyTorch Metric Learning."""

from __future__ import annotations

import tempfile
from pathlib import Path

import torch

from pytorch_metric_learning import losses, trainers
from pytorch_metric_learning.samplers import MPerClassSampler
from pytorch_metric_learning.testers import GlobalEmbeddingSpaceTester
from pytorch_metric_learning.utils import accuracy_calculator, logging_presets
from pytorch_metric_learning.utils.common_functions import EmbeddingDataset


def build_dataset() -> EmbeddingDataset:
    data = torch.tensor(
        [
            [1.0, 0.0],
            [0.9, 0.1],
            [-1.0, 0.0],
            [-0.9, -0.1],
            [0.0, 1.0],
            [0.1, 0.9],
            [0.0, -1.0],
            [-0.1, -0.9],
        ],
        dtype=torch.float32,
    )
    labels = torch.tensor([0, 0, 1, 1, 2, 2, 3, 3])
    return EmbeddingDataset(data, labels)


def main() -> None:
    torch.manual_seed(11)
    dataset = build_dataset()
    labels = dataset.labels

    trunk = torch.nn.Linear(2, 2)
    embedder = torch.nn.Linear(2, 2)
    trunk_optimizer = torch.optim.SGD(trunk.parameters(), lr=0.1)
    embedder_optimizer = torch.optim.SGD(embedder.parameters(), lr=0.1)
    sampler = MPerClassSampler(labels, m=2, batch_size=4, length_before_new_iter=8)

    with tempfile.TemporaryDirectory(prefix="pml-training-smoke-") as tmpdir:
        tmp = Path(tmpdir)
        model_folder = tmp / "models"
        logs_folder = tmp / "logs"
        tensorboard_folder = tmp / "tensorboard"

        record_keeper, _, _ = logging_presets.get_record_keeper(
            str(logs_folder), str(tensorboard_folder)
        )
        hooks = logging_presets.get_hook_container(
            record_keeper,
            primary_metric="precision_at_1",
            log_freq=1,
        )

        tester = GlobalEmbeddingSpaceTester(
            accuracy_calculator=accuracy_calculator.AccuracyCalculator(
                include=("precision_at_1",), k=1
            ),
            batch_size=2,
            dataloader_num_workers=0,
            end_of_testing_hook=hooks.end_of_testing_hook,
            data_device=torch.device("cpu"),
        )
        end_of_epoch_hook = hooks.end_of_epoch_hook(
            tester,
            {"train": dataset, "val": dataset},
            str(model_folder),
            test_interval=1,
        )

        trainer = trainers.MetricLossOnly(
            models={"trunk": trunk, "embedder": embedder},
            optimizers={
                "trunk_optimizer": trunk_optimizer,
                "embedder_optimizer": embedder_optimizer,
            },
            batch_size=4,
            loss_funcs={"metric_loss": losses.TripletMarginLoss()},
            dataset=dataset,
            mining_funcs={},
            iterations_per_epoch=2,
            sampler=sampler,
            data_device=torch.device("cpu"),
            dataloader_num_workers=0,
            end_of_iteration_hook=hooks.end_of_iteration_hook,
            end_of_epoch_hook=end_of_epoch_hook,
        )

        trainer.train(num_epochs=1)
        assert hooks.get_loss_history()
        assert model_folder.exists()
        print("training-smoke-ok")


if __name__ == "__main__":
    main()
