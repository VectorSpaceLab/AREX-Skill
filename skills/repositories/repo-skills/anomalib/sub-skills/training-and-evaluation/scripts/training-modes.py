#!/usr/bin/env python3
"""CPU-only smoke for Anomalib training modes.

This helper exercises two behaviors that frequently get confused:

- normal mode keeps the default checkpoint path and returns metrics
- barebones mode skips the default checkpoint path but still returns the same
  metric keys and values when the Anomalib evaluator is attached
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import torch
from lightning import seed_everything
from torch import nn
from torch.utils.data import DataLoader, Dataset

from anomalib import LearningType
from anomalib.data import ImageBatch, InferenceBatch
from anomalib.engine import Engine
from anomalib.models.components.base import AnomalibModule

SEED = 7
IMAGE_SIZE = 8
SENSITIVITY = 0.9


class TinyImageDataset(Dataset):
    """Deterministic image dataset for the training-mode smoke."""

    def __init__(self) -> None:
        self.samples: list[tuple[torch.Tensor, int, torch.Tensor]] = []
        for index, label in enumerate([0, 1, 0, 1]):
            image = torch.zeros(3, IMAGE_SIZE, IMAGE_SIZE, dtype=torch.float32)
            mask = torch.zeros(IMAGE_SIZE, IMAGE_SIZE, dtype=torch.int64)
            if label:
                image[:, 2:6, 2:6] = 1.0
                mask[2:6, 2:6] = 1
            else:
                image += 0.05 * (index + 1)
            self.samples.append((image, label, mask))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int, torch.Tensor]:
        return self.samples[index]


def collate_samples(samples: list[tuple[torch.Tensor, int, torch.Tensor]]) -> ImageBatch:
    """Pack the synthetic samples into an Anomalib image batch."""

    images, labels, masks = zip(*samples, strict=True)
    return ImageBatch(
        image=torch.stack(list(images)),
        gt_label=torch.tensor(labels, dtype=torch.int64),
        gt_mask=torch.stack(list(masks)),
    )


class TinyScorer(nn.Module):
    """Minimal scorer that produces both image scores and anomaly maps."""

    def __init__(self) -> None:
        super().__init__()
        self.scale = nn.Parameter(torch.tensor(1.0))

    def forward(self, images: torch.Tensor) -> InferenceBatch:
        anomaly_map = images.mean(dim=1) * self.scale
        pred_score = anomaly_map.amax(dim=(-2, -1))
        return InferenceBatch(pred_score=pred_score, anomaly_map=anomaly_map)


class TinyAnomalibModule(AnomalibModule):
    """Tiny Anomalib model used to exercise training modes."""

    def __init__(self, sensitivity: float = SENSITIVITY) -> None:
        super().__init__(pre_processor=False, post_processor=True, evaluator=True, visualizer=False)
        self.post_processor.image_sensitivity = sensitivity
        self.post_processor.pixel_sensitivity = sensitivity
        self.model = TinyScorer()

    @property
    def trainer_arguments(self) -> dict[str, int]:
        return {"max_epochs": 1, "num_sanity_val_steps": 0}

    @property
    def learning_type(self) -> LearningType:
        return LearningType.ONE_CLASS

    def configure_optimizers(self) -> torch.optim.Optimizer:
        return torch.optim.SGD(self.parameters(), lr=0.0)

    def training_step(self, batch: ImageBatch, batch_idx: int) -> torch.Tensor:
        del batch_idx
        predictions = self.model(batch.image)
        loss = torch.nn.functional.mse_loss(predictions.pred_score, batch.gt_label.float())
        return loss * 0.0

    def validation_step(self, batch: ImageBatch, batch_idx: int) -> ImageBatch:
        del batch_idx
        predictions = self.model(batch.image)
        return batch.update(pred_score=predictions.pred_score, anomaly_map=predictions.anomaly_map)


def as_floats(metrics: dict[str, Any]) -> dict[str, float]:
    """Convert tensor-like metric outputs to plain floats."""

    converted: dict[str, float] = {}
    for key, value in metrics.items():
        converted[key] = float(value.item()) if hasattr(value, "item") else float(value)
    return converted


def run_mode(*, barebones: bool) -> tuple[dict[str, float], int]:
    """Run one training mode and return its metrics and checkpoint count."""

    seed_everything(SEED, workers=True)
    dataset = TinyImageDataset()
    dataloader = DataLoader(dataset, batch_size=4, shuffle=False, collate_fn=collate_samples, num_workers=0)

    with tempfile.TemporaryDirectory(prefix=f"anomalib-training-mode-{barebones}-") as temp_dir:
        root_dir = Path(temp_dir)
        model = TinyAnomalibModule()
        engine = Engine(
            default_root_dir=root_dir,
            accelerator="cpu",
            devices=1,
            logger=False,
            enable_progress_bar=False,
            limit_train_batches=1,
            limit_val_batches=1,
            limit_test_batches=1,
            num_sanity_val_steps=0,
            max_epochs=1,
            barebones=barebones,
        )
        engine.fit(model=model, train_dataloaders=dataloader, val_dataloaders=dataloader)
        results = engine.test(model=model, dataloaders=dataloader, verbose=False)
        metrics = as_floats(results[0])
        checkpoint_count = len(list(root_dir.rglob("*.ckpt")))
        return metrics, checkpoint_count


def main() -> None:
    normal_metrics, normal_checkpoints = run_mode(barebones=False)
    barebones_metrics, barebones_checkpoints = run_mode(barebones=True)

    assert normal_metrics.keys() == barebones_metrics.keys(), (normal_metrics, barebones_metrics)
    for key in normal_metrics:
        assert abs(normal_metrics[key] - barebones_metrics[key]) < 1e-6, (key, normal_metrics[key], barebones_metrics[key])

    expected = {"image_AUROC", "image_F1Score", "pixel_AUROC", "pixel_F1Score"}
    assert expected.issubset(normal_metrics), normal_metrics
    assert normal_metrics["image_AUROC"] == 1.0
    assert normal_metrics["image_F1Score"] == 1.0
    assert normal_metrics["pixel_AUROC"] == 1.0
    assert normal_metrics["pixel_F1Score"] == 1.0

    assert normal_checkpoints > 0, normal_checkpoints
    assert barebones_checkpoints == 0, barebones_checkpoints

    print("training-mode smoke passed")
    print("normal:", normal_metrics, "checkpoints:", normal_checkpoints)
    print("barebones:", barebones_metrics, "checkpoints:", barebones_checkpoints)


if __name__ == "__main__":
    main()
