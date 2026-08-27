#!/usr/bin/env python3
"""CPU-only smoke for metrics, preprocessing, post-processing, and visualization.

This helper is intentionally tiny and deterministic. It checks the core failure
modes that usually show up before training ever starts:

- duplicate metric names without prefixes
- missing or optional metric fields
- preprocessing shape expectations
- post-processing threshold handoff
- direct image visualization
"""

from __future__ import annotations

import torch
from PIL import Image
from torchvision.transforms.v2 import Compose, Resize, ToDtype, ToImage

from anomalib.data import ImageBatch, ImageItem, InferenceBatch
from anomalib.metrics import AUROC, F1Score
from anomalib.post_processing import PostProcessor
from anomalib.pre_processing import PreProcessor
from anomalib.visualization import ImageVisualizer

SEED = 13


def metric_smoke() -> None:
    """Exercise field binding, prefixes, and strict/non-strict metric behavior."""

    torch.manual_seed(SEED)

    unprefixed_image_f1 = F1Score(fields=["pred_label", "gt_label"])
    unprefixed_pixel_f1 = F1Score(fields=["pred_mask", "gt_mask"])
    assert unprefixed_image_f1.name == "F1Score"
    assert unprefixed_pixel_f1.name == "F1Score"

    image_f1 = F1Score(fields=["pred_label", "gt_label"], prefix="image_")
    pixel_f1 = F1Score(fields=["pred_mask", "gt_mask"], prefix="pixel_")
    assert image_f1.name == "image_F1Score"
    assert pixel_f1.name == "pixel_F1Score"

    good_batch = ImageBatch(
        image=torch.rand(2, 3, 4, 4),
        pred_score=torch.tensor([0.1, 0.9]),
        pred_label=torch.tensor([0, 1]),
        pred_mask=torch.tensor(
            [
                [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]],
                [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]],
            ],
            dtype=torch.int64,
        ),
        gt_label=torch.tensor([0, 1]),
        gt_mask=torch.tensor(
            [
                [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]],
                [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]],
            ],
            dtype=torch.int64,
        ),
    )

    image_f1.update(good_batch)
    pixel_f1.update(good_batch)
    assert image_f1.compute().item() == 1.0
    assert pixel_f1.compute().item() == 1.0

    missing_score_batch = ImageBatch(image=torch.rand(2, 3, 4, 4), gt_label=torch.tensor([0, 1]))
    strict_metric = AUROC(fields=["pred_score", "gt_label"])
    try:
        strict_metric.update(missing_score_batch)
        raise AssertionError("strict metric should have raised a ValueError")
    except ValueError as exc:
        assert "field with name pred_score" in str(exc)

    relaxed_metric = AUROC(fields=["pred_score", "gt_label"], strict=False)
    relaxed_metric.update(missing_score_batch)
    assert relaxed_metric._update_count == 0  # noqa: SLF001
    assert relaxed_metric.update_called is False


def preprocessing_smoke() -> None:
    """Check that batch tensors are resized as expected."""

    pre_processor = PreProcessor(
        transform=Compose([
            Resize((4, 4)),
            ToImage(),
            ToDtype(torch.float32, scale=True),
        ]),
    )
    processed = pre_processor(torch.rand(1, 3, 8, 8))
    assert processed.shape == (1, 3, 4, 4)


def postprocessing_smoke() -> None:
    """Check threshold collection and inference-time formatting."""

    validation_batch = ImageBatch(
        image=torch.rand(2, 3, 4, 4),
        pred_score=torch.tensor([0.0, 1.0]),
        gt_label=torch.tensor([0, 1]),
        anomaly_map=torch.stack([torch.zeros(4, 4), torch.ones(4, 4)]),
        gt_mask=torch.stack([torch.zeros(4, 4, dtype=torch.int64), torch.ones(4, 4, dtype=torch.int64)]),
    )
    post_processor = PostProcessor(image_sensitivity=0.9, pixel_sensitivity=0.9)
    post_processor.on_validation_batch_end(None, None, validation_batch)
    post_processor.on_validation_epoch_end(None, None)

    assert not torch.isnan(post_processor.image_threshold).item()
    assert not torch.isnan(post_processor.pixel_threshold).item()

    inference = post_processor(
        InferenceBatch(
            pred_score=torch.tensor([0.0, 1.0]),
            anomaly_map=torch.stack([torch.zeros(4, 4), torch.ones(4, 4)]),
        ),
    )
    assert inference.pred_label is not None
    assert inference.pred_mask is not None
    assert inference.pred_label.shape == (2,)
    assert inference.pred_mask.shape == (2, 4, 4)


def visualization_smoke() -> None:
    """Check that a small anomaly item can be visualized directly."""

    item = ImageItem(
        image=torch.rand(3, 4, 4),
        pred_mask=torch.ones(4, 4, dtype=torch.bool),
        gt_mask=torch.zeros(4, 4, dtype=torch.bool),
        anomaly_map=torch.rand(4, 4),
        gt_label=torch.tensor(1),
    )
    visualizer = ImageVisualizer(
        fields=["image", "anomaly_map"],
        overlay_fields=[("image", ["gt_mask", "pred_mask"])],
        field_size=(8, 8),
        text_config={"enable": False},
    )
    rendered = visualizer(item)
    assert isinstance(rendered, Image.Image)
    assert rendered.size[0] > 0 and rendered.size[1] > 0


def main() -> None:
    metric_smoke()
    preprocessing_smoke()
    postprocessing_smoke()
    visualization_smoke()
    print("evaluation smoke passed")


if __name__ == "__main__":
    main()
