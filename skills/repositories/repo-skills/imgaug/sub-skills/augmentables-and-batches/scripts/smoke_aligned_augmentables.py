#!/usr/bin/env python3
"""Tiny smoke for imgaug image+augmentable alignment.

Safe default:
- tiny in-memory arrays
- no GUI
- no network

Example:
    python sub-skills/augmentables-and-batches/scripts/smoke_aligned_augmentables.py
"""

from __future__ import annotations

import numpy as np


def main() -> int:
    import imgaug as ia
    import imgaug.augmenters as iaa
    from imgaug.augmentables.batches import UnnormalizedBatch

    image = np.zeros((16, 16, 3), dtype=np.uint8)
    image[4:12, 4:12] = 255
    kpsoi = ia.KeypointsOnImage([ia.Keypoint(x=4.0, y=5.0)], shape=image.shape)
    bbsoi = ia.BoundingBoxesOnImage([ia.BoundingBox(x1=3, y1=3, x2=10, y2=11)], shape=image.shape)
    hm = ia.HeatmapsOnImage(np.zeros((8, 8, 1), dtype=np.float32), shape=image.shape)
    sm = ia.SegmentationMapsOnImage(np.zeros((8, 8, 1), dtype=np.int32), shape=image.shape)

    seq = iaa.Sequential([iaa.Fliplr(1.0), iaa.Affine(translate_px={"x": 1})])
    images_aug, kps_aug, bbs_aug, hm_aug, sm_aug = seq(
        images=np.array([image]),
        keypoints=[kpsoi],
        bounding_boxes=[bbsoi],
        heatmaps=[hm],
        segmentation_maps=[sm],
    )

    assert images_aug.shape == (1, 16, 16, 3)
    assert len(kps_aug) == 1 and len(kps_aug[0].keypoints) == 1
    assert len(bbs_aug) == 1 and len(bbs_aug[0].bounding_boxes) == 1
    assert hm_aug[0].arr_0to1.shape == (8, 8, 1)
    assert sm_aug[0].arr.shape == (8, 8, 1)

    batch = UnnormalizedBatch(images=np.array([image]), keypoints=[kpsoi], data={"id": "tiny"})
    batch_aug = seq.augment_batch_(batch)
    assert batch_aug.images_aug is not None
    assert batch_aug.keypoints_aug is not None
    assert batch_aug.data["id"] == "tiny"

    print("aligned augmentables smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
