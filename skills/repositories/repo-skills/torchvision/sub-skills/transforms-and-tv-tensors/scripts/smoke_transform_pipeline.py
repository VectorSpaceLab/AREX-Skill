#!/usr/bin/env python3
"""Tiny no-download smoke check for torchvision v2 transforms and TVTensors."""

import torch
from torchvision import tv_tensors
from torchvision.transforms import v2


def main() -> None:
    torch.manual_seed(0)

    height, width = 16, 20
    image = tv_tensors.Image(torch.arange(3 * height * width, dtype=torch.uint8).reshape(3, height, width))
    boxes = tv_tensors.BoundingBoxes(
        torch.tensor([[1, 2, 8, 10], [6, 4, 18, 15]], dtype=torch.float32),
        format="XYXY",
        canvas_size=(height, width),
    )
    masks = tv_tensors.Mask(torch.zeros((2, height, width), dtype=torch.uint8))
    masks[0, 2:10, 1:8] = 1
    masks[1, 4:15, 6:18] = 1

    sample = {
        "image": image,
        "target": {
            "boxes": boxes,
            "labels": torch.tensor([5, 9]),
            "masks": masks,
            "sample_id": "tiny-smoke",
        },
    }

    def labels_getter(sample):
        return sample["target"]["labels"]

    transforms = v2.Compose(
        [
            v2.RandomHorizontalFlip(p=1.0),
            v2.Resize((8, 10), antialias=True),
            v2.ClampBoundingBoxes(),
            v2.SanitizeBoundingBoxes(labels_getter=labels_getter),
            v2.ToDtype(torch.float32, scale=True),
        ]
    )

    output = transforms(sample)
    out_image = output["image"]
    out_target = output["target"]
    out_boxes = out_target["boxes"]
    out_masks = out_target["masks"]

    assert isinstance(out_image, tv_tensors.Image), type(out_image)
    assert isinstance(out_boxes, tv_tensors.BoundingBoxes), type(out_boxes)
    assert isinstance(out_masks, tv_tensors.Mask), type(out_masks)
    assert out_image.shape == (3, 8, 10), out_image.shape
    assert out_image.dtype == torch.float32, out_image.dtype
    assert float(out_image.min()) >= 0.0 and float(out_image.max()) <= 1.0
    assert out_boxes.canvas_size == (8, 10), out_boxes.canvas_size
    assert out_boxes.shape[-1] == 4, out_boxes.shape
    assert out_masks.shape[-2:] == (8, 10), out_masks.shape
    assert out_target["labels"].shape[0] == out_boxes.shape[0]
    assert out_target["sample_id"] == "tiny-smoke"

    print("ok: v2 transform pipeline preserved TVTensor metadata")
    print(f"image={tuple(out_image.shape)} {out_image.dtype}")
    print(f"boxes={out_boxes.tolist()} canvas_size={out_boxes.canvas_size}")


if __name__ == "__main__":
    main()
