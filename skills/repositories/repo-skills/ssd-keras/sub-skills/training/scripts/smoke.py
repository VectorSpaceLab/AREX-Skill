#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

RUNTIME_SRC = None


def assert_bundled_module(module_name: str) -> None:
    module = sys.modules.get(module_name) or __import__(module_name)
    module_file = getattr(module, "__file__", None)
    if RUNTIME_SRC is None or module_file is None:
        raise RuntimeError(f"Cannot verify bundled location for {module_name}")
    resolved = Path(module_file).resolve()
    try:
        resolved.relative_to(RUNTIME_SRC)
    except ValueError as exc:
        raise RuntimeError(f"{module_name} imported from {resolved}, expected it under {RUNTIME_SRC}") from exc


def locate_skill_root() -> Path:
    script_path = Path(__file__).resolve()
    for parent in script_path.parents:
        if (parent / "SKILL.md").is_file() and (parent / "runtime-src").is_dir():
            return parent
    raise FileNotFoundError("Could not locate the bundled SSD Keras skill root or its runtime-src directory.")


def add_runtime_source() -> tuple[Path, Path]:
    global RUNTIME_SRC
    skill_root = locate_skill_root()
    runtime_src = skill_root / "runtime-src"
    if str(runtime_src) not in sys.path:
        sys.path.insert(0, str(runtime_src))
    RUNTIME_SRC = runtime_src.resolve()
    return skill_root, runtime_src


def make_image(path: Path, size: tuple[int, int] = (300, 300)) -> None:
    image = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    image[80:220, 80:220] = [64, 128, 255]
    Image.fromarray(image).save(path)


def batch_summary(batch) -> str:
    if isinstance(batch, (tuple, list)):
        return ", ".join(str(item.shape) if hasattr(item, "shape") else type(item).__name__ for item in batch)
    if hasattr(batch, "shape"):
        return str(batch.shape)
    return type(batch).__name__


def smoke_train_step(base: Path) -> None:
    from keras.optimizers import SGD

    from data_generator.object_detection_2d_data_generator import DataGenerator
    from data_generator.object_detection_2d_geometric_ops import Resize
    from data_generator.object_detection_2d_photometric_ops import ConvertTo3Channels
    from keras_loss_function.keras_ssd_loss import SSDLoss
    from models.keras_ssd7 import build_model
    from ssd_encoder_decoder.ssd_input_encoder import SSDInputEncoder

    for package_name in ["data_generator", "keras_loss_function", "keras_layers", "models", "ssd_encoder_decoder", "bounding_box_utils"]:
        assert_bundled_module(package_name)

    image_path = base / "sample.jpg"
    make_image(image_path)

    model, predictor_sizes = build_model(
        image_size=(300, 300, 3),
        n_classes=1,
        mode="training",
        return_predictor_sizes=True,
    )
    encoder = SSDInputEncoder(
        img_height=300,
        img_width=300,
        n_classes=1,
        predictor_sizes=predictor_sizes,
        normalize_coords=False,
    )

    dataset = DataGenerator(
        load_images_into_memory=False,
        filenames=[str(image_path)],
        labels=[np.array([[1, 80, 80, 220, 220]], dtype=np.float32)],
        image_ids=["sample"],
    )
    generator = dataset.generate(
        batch_size=1,
        shuffle=False,
        transformations=[ConvertTo3Channels(), Resize(height=300, width=300)],
        label_encoder=encoder,
        returns={"processed_images", "encoded_labels"},
        keep_images_without_gt=True,
    )
    batch_x, batch_y = next(generator)
    print(f"train batch: {batch_summary((batch_x, batch_y))}")

    ssd_loss = SSDLoss(neg_pos_ratio=3, n_neg_min=0, alpha=1.0)
    model.compile(optimizer=SGD(lr=0.001, momentum=0.9), loss=ssd_loss.compute_loss)
    loss = model.train_on_batch(batch_x, batch_y)
    print(f"train loss: {loss}")


def smoke_weight_sampling() -> None:
    from misc_utils.tensor_sampling_utils import sample_tensors
    assert_bundled_module("misc_utils")

    kernel = np.arange(2 * 2 * 3 * 4, dtype=np.float32).reshape(2, 2, 3, 4)
    bias = np.arange(4, dtype=np.float32)
    sampled_kernel, sampled_bias = sample_tensors(
        [kernel, bias],
        sampling_instructions=[2, 2, 3, 2],
        axes=[[3]],
        init=["zeros", "zeros"],
    )
    print(f"sampled kernel shape: {sampled_kernel.shape}")
    print(f"sampled bias shape: {sampled_bias.shape}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Synthetic training smoke for the bundled SSD Keras skill.")
    parser.add_argument("--skip-train-step", action="store_true", help="Only run the weight-sampling smoke.")
    args = parser.parse_args()

    skill_root, runtime_src = add_runtime_source()
    print(f"skill-root: {skill_root}")
    print(f"runtime-source: {runtime_src}")

    if not args.skip_train_step:
        with tempfile.TemporaryDirectory(prefix="ssd-keras-training-smoke-") as tmp:
            smoke_train_step(Path(tmp))

    smoke_weight_sampling()
    print("training smoke complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
