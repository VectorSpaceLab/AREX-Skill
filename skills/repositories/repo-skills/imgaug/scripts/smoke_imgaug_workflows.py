#!/usr/bin/env python3
"""Run tiny imgaug workflow smokes that mirror the documented usage patterns.

Safe default:
- tiny in-memory arrays only
- no GUI
- no network
- no large loops

Example:
    python scripts/smoke_imgaug_workflows.py
"""

from __future__ import annotations

import numpy as np


def _assert(cond: bool, message: str) -> None:
    if not cond:
        raise SystemExit(message)


def simple_image_pipeline() -> None:
    import imgaug.augmenters as iaa

    images = np.zeros((4, 8, 8, 3), dtype=np.uint8)
    images[:, :, 0, :] = 10
    seq = iaa.Sequential([
        iaa.Fliplr(1.0),
        iaa.Affine(rotate=0),
        iaa.GaussianBlur(sigma=0.0),
        iaa.Add(1),
    ])
    out = seq(images=images)
    _assert(out.shape == images.shape, f"shape changed: {out.shape}")
    _assert(out.dtype == images.dtype, f"dtype changed: {out.dtype}")
    _assert(int(out[0, 0, -1, 0]) == 11, "expected additive smoke pixel to change")


def aligned_augmentables() -> None:
    import imgaug as ia
    import imgaug.augmenters as iaa

    image = np.zeros((16, 16, 3), dtype=np.uint8)
    image[4:12, 4:12] = 255
    images = np.stack([image, image], axis=0)
    keypoints = [
        [ia.Keypoint(x=5.0, y=5.0)],
        [ia.Keypoint(x=10.0, y=10.0)],
    ]
    bbs = [
        [ia.BoundingBox(x1=3, y1=3, x2=11, y2=11)],
        [ia.BoundingBox(x1=4, y1=4, x2=12, y2=12)],
    ]
    heatmaps = np.zeros((2, 8, 8, 1), dtype=np.float32)
    segmaps = np.zeros((2, 8, 8, 1), dtype=np.int32)
    seq = iaa.Sequential([
        iaa.Fliplr(1.0),
        iaa.Affine(translate_px={"x": 1, "y": 0}),
    ])
    images_aug, keypoints_aug, bbs_aug, heatmaps_aug, segmaps_aug = seq(
        images=images,
        keypoints=keypoints,
        bounding_boxes=bbs,
        heatmaps=heatmaps,
        segmentation_maps=segmaps,
    )
    _assert(images_aug.shape == images.shape, "aligned image smoke failed")
    _assert(len(keypoints_aug) == 2 and len(keypoints_aug[0]) == 1, "keypoints count changed")
    _assert(len(bbs_aug) == 2 and len(bbs_aug[0]) == 1, "boxes count changed")
    _assert(heatmaps_aug.shape == heatmaps.shape, "heatmaps shape changed")
    _assert(segmaps_aug.shape == segmaps.shape, "segmaps shape changed")


def deterministic_replay() -> None:
    import imgaug.augmenters as iaa

    images = np.zeros((1, 8, 8, 3), dtype=np.uint8)
    seq = iaa.Sequential([iaa.Fliplr(0.5), iaa.Add((0, 2))])
    det = seq.to_deterministic()
    out1 = det(images=images)
    out2 = det(images=images)
    _assert(np.array_equal(out1, out2), "deterministic replay mismatch")


def main() -> int:
    simple_image_pipeline()
    aligned_augmentables()
    deterministic_replay()
    print("imgaug smoke workflows passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
