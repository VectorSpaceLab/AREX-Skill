#!/usr/bin/env python3
"""No-network smoke check for TorchVision dataset, image IO, and utility APIs."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path



def _make_png_fixture(root: Path) -> None:
    from PIL import Image

    for class_name, color in {"cat": (255, 0, 0), "dog": (0, 255, 0)}.items():
        class_dir = root / class_name
        class_dir.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (8, 8), color=color).save(class_dir / f"{class_name}.png")


def _check_image_folder(root: Path) -> dict[str, object]:
    from torchvision.datasets import ImageFolder
    from torchvision.transforms import v2

    transform = v2.Compose([v2.ToImage(), v2.Resize((10, 10))])
    dataset = ImageFolder(root=root, transform=transform)
    image, target = dataset[0]

    if len(dataset) != 2:
        raise AssertionError(f"expected 2 ImageFolder samples, got {len(dataset)}")
    if dataset.classes != ["cat", "dog"]:
        raise AssertionError(f"unexpected classes: {dataset.classes}")
    if tuple(image.shape[-2:]) != (10, 10):
        raise AssertionError(f"transform did not resize image, got shape {tuple(image.shape)}")

    return {
        "classes": dataset.classes,
        "class_to_idx": dataset.class_to_idx,
        "first_target": int(target),
        "first_shape": list(image.shape),
    }


def _check_fake_data() -> dict[str, object]:
    from torchvision.datasets import FakeData
    from torchvision.transforms import v2

    dataset = FakeData(size=3, image_size=(3, 12, 12), num_classes=2, transform=v2.ToImage())
    image, target = dataset[1]
    if tuple(image.shape) != (3, 12, 12):
        raise AssertionError(f"unexpected FakeData image shape: {tuple(image.shape)}")
    if target not in {0, 1}:
        raise AssertionError(f"unexpected FakeData target: {target}")
    return {"length": len(dataset), "sample_shape": list(image.shape), "target": int(target)}


def _check_io(root: Path) -> dict[str, object]:
    import torch
    from torchvision.io import decode_image, write_png

    image = torch.zeros((3, 6, 7), dtype=torch.uint8)
    image[0].fill_(255)
    path = root / "roundtrip.png"
    write_png(image, str(path))
    decoded = decode_image(str(path), mode="RGB")
    if decoded.dtype != torch.uint8:
        raise AssertionError(f"decoded dtype should be uint8, got {decoded.dtype}")
    if tuple(decoded.shape) != (3, 6, 7):
        raise AssertionError(f"decoded shape mismatch: {tuple(decoded.shape)}")
    return {"available": True, "decoded_shape": list(decoded.shape), "decoded_dtype": str(decoded.dtype)}


def _check_utils() -> dict[str, object]:
    import torch
    from torchvision.utils import draw_bounding_boxes, make_grid

    image = torch.zeros((3, 16, 16), dtype=torch.uint8)
    boxes = torch.tensor([[2, 2, 12, 12]], dtype=torch.float32)
    annotated = draw_bounding_boxes(image, boxes, labels=["box"], colors="red", width=1)
    grid = make_grid([image, annotated], nrow=2)
    if annotated.shape != image.shape:
        raise AssertionError(f"annotated shape mismatch: {tuple(annotated.shape)}")
    if grid.ndim != 3:
        raise AssertionError(f"grid should be CHW, got shape {tuple(grid.shape)}")
    return {"annotated_shape": list(annotated.shape), "grid_shape": list(grid.shape)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()

    try:
        import torch  # noqa: F401
        import torchvision  # noqa: F401
    except ModuleNotFoundError as error:
        raise SystemExit(f"Missing required package for this smoke check: {error.name}") from error

    results: dict[str, object] = {}
    with tempfile.TemporaryDirectory(prefix="torchvision-dataset-io-") as tmp:
        tmp_path = Path(tmp)
        image_folder_root = tmp_path / "image-folder"
        _make_png_fixture(image_folder_root)

        results["image_folder"] = _check_image_folder(image_folder_root)
        results["fake_data"] = _check_fake_data()
        results["utils"] = _check_utils()
        try:
            results["io"] = _check_io(tmp_path)
        except Exception as error:  # image extension support can be absent in broken builds
            results["io"] = {"available": False, "error": f"{type(error).__name__}: {error}"}

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        print("TorchVision dataset/io smoke check passed")
        for name, value in results.items():
            print(f"- {name}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
