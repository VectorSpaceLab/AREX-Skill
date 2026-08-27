#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
from pathlib import Path
from xml.etree.ElementTree import Element, ElementTree, SubElement

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


def make_image(path: Path, size: tuple[int, int] = (32, 32)) -> None:
    image = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    image[8:24, 8:24] = [255, 64, 64]
    Image.fromarray(image).save(path)


def write_csv_fixture(base: Path, image_name: str) -> Path:
    csv_path = base / "labels.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["image_name", "class_id", "xmin", "xmax", "ymin", "ymax"])
        writer.writerow([image_name, 1, 8, 24, 8, 24])
    return csv_path


def write_voc_fixture(base: Path, image_name: str) -> tuple[Path, Path, Path]:
    base.mkdir(parents=True, exist_ok=True)
    images_dir = base / "voc_images"
    annotations_dir = base / "voc_annotations"
    images_dir.mkdir()
    annotations_dir.mkdir()
    make_image(images_dir / image_name)

    image_set_file = base / "voc_test.txt"
    image_set_file.write_text("sample\n")

    annotation = Element("annotation")
    SubElement(annotation, "folder").text = "voc_images"
    SubElement(annotation, "filename").text = image_name
    size = SubElement(annotation, "size")
    SubElement(size, "width").text = "32"
    SubElement(size, "height").text = "32"
    SubElement(size, "depth").text = "3"
    obj = SubElement(annotation, "object")
    SubElement(obj, "name").text = "cat"
    SubElement(obj, "pose").text = "Unspecified"
    SubElement(obj, "truncated").text = "0"
    SubElement(obj, "difficult").text = "0"
    bbox = SubElement(obj, "bndbox")
    SubElement(bbox, "xmin").text = "8"
    SubElement(bbox, "ymin").text = "8"
    SubElement(bbox, "xmax").text = "24"
    SubElement(bbox, "ymax").text = "24"
    ElementTree(annotation).write(annotations_dir / "sample.xml")

    return images_dir, image_set_file, annotations_dir


def write_coco_fixture(base: Path, image_name: str) -> tuple[Path, Path]:
    base.mkdir(parents=True, exist_ok=True)
    images_dir = base / "coco_images"
    images_dir.mkdir()
    make_image(images_dir / image_name)
    annotations_path = base / "coco.json"
    coco = {
        "images": [
            {"id": 1, "file_name": image_name, "width": 32, "height": 32},
        ],
        "annotations": [
            {
                "id": 1,
                "image_id": 1,
                "category_id": 1,
                "bbox": [8, 8, 16, 16],
                "area": 256,
                "iscrowd": 0,
            }
        ],
        "categories": [
            {"id": 1, "name": "cat"},
        ],
    }
    annotations_path.write_text(json.dumps(coco))
    return images_dir, annotations_path


def batch_summary(batch) -> str:
    if isinstance(batch, (tuple, list)):
        items = []
        for item in batch:
            if item is None:
                items.append("None")
            elif hasattr(item, "shape"):
                items.append(str(item.shape))
            else:
                items.append(type(item).__name__)
        return ", ".join(items)
    if hasattr(batch, "shape"):
        return str(batch.shape)
    return type(batch).__name__


def smoke_csv(base: Path) -> None:
    base.mkdir(parents=True, exist_ok=True)
    from data_generator.object_detection_2d_data_generator import DataGenerator
    from data_generator.object_detection_2d_geometric_ops import Resize
    from data_generator.object_detection_2d_photometric_ops import ConvertTo3Channels
    for package_name in ["data_generator", "ssd_encoder_decoder", "bounding_box_utils"]:
        assert_bundled_module(package_name)

    image_name = "sample.jpg"
    images_dir = base / "csv_images"
    images_dir.mkdir()
    make_image(images_dir / image_name)
    csv_path = write_csv_fixture(base, image_name)

    dataset = DataGenerator(load_images_into_memory=False)
    dataset.parse_csv(
        images_dir=str(images_dir),
        labels_filename=str(csv_path),
        input_format=["image_name", "class_id", "xmin", "xmax", "ymin", "ymax"],
    )
    generator = dataset.generate(
        batch_size=1,
        shuffle=False,
        transformations=[ConvertTo3Channels(), Resize(height=32, width=32)],
        label_encoder=None,
        returns={"processed_images", "processed_labels", "filenames", "image_ids"},
        keep_images_without_gt=True,
    )
    batch = next(generator)
    print(f"csv size: {dataset.get_dataset_size()}")
    print(f"csv batch: {batch_summary(batch)}")

    hdf5_path = base / "dataset.h5"
    dataset.create_hdf5_dataset(file_path=str(hdf5_path), resize=False, variable_image_size=True, verbose=False)
    cached = DataGenerator(hdf5_dataset_path=str(hdf5_path))
    cached_generator = cached.generate(batch_size=1, shuffle=False, returns={"processed_images", "processed_labels"})
    cached_batch = next(cached_generator)
    print(f"hdf5 size: {cached.get_dataset_size()}")
    print(f"hdf5 batch: {batch_summary(cached_batch)}")


def smoke_voc(base: Path) -> None:
    from data_generator.object_detection_2d_data_generator import DataGenerator
    from data_generator.object_detection_2d_geometric_ops import Resize
    from data_generator.object_detection_2d_photometric_ops import ConvertTo3Channels
    assert_bundled_module("data_generator")

    image_name = "sample.jpg"
    images_dir, image_set_file, annotations_dir = write_voc_fixture(base, image_name)
    dataset = DataGenerator(load_images_into_memory=False)
    dataset.parse_xml(
        images_dirs=[str(images_dir)],
        image_set_filenames=[str(image_set_file)],
        annotations_dirs=[str(annotations_dir)],
        classes=[
            "background",
            "cat",
        ],
    )
    generator = dataset.generate(
        batch_size=1,
        shuffle=False,
        transformations=[ConvertTo3Channels(), Resize(height=32, width=32)],
        returns={"processed_images", "processed_labels", "filenames", "image_ids"},
        keep_images_without_gt=True,
    )
    batch = next(generator)
    print(f"voc size: {dataset.get_dataset_size()}")
    print(f"voc batch: {batch_summary(batch)}")


def smoke_coco(base: Path) -> None:
    from data_generator.object_detection_2d_data_generator import DataGenerator
    from data_generator.object_detection_2d_geometric_ops import Resize
    from data_generator.object_detection_2d_photometric_ops import ConvertTo3Channels
    assert_bundled_module("data_generator")

    image_name = "sample.jpg"
    images_dir, annotations_path = write_coco_fixture(base, image_name)
    dataset = DataGenerator(load_images_into_memory=False)
    dataset.parse_json(
        images_dirs=[str(images_dir)],
        annotations_filenames=[str(annotations_path)],
        ground_truth_available=True,
    )
    generator = dataset.generate(
        batch_size=1,
        shuffle=False,
        transformations=[ConvertTo3Channels(), Resize(height=32, width=32)],
        returns={"processed_images", "processed_labels", "filenames", "image_ids"},
        keep_images_without_gt=True,
    )
    batch = next(generator)
    print(f"coco size: {dataset.get_dataset_size()}")
    print(f"coco batch: {batch_summary(batch)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Synthetic data-preparation smoke for the bundled SSD Keras skill.")
    parser.add_argument(
        "--mode",
        choices=["csv", "voc", "coco", "all"],
        default="all",
        help="Which synthetic parser flow to run.",
    )
    args = parser.parse_args()

    skill_root, runtime_src = add_runtime_source()
    print(f"skill-root: {skill_root}")
    print(f"runtime-source: {runtime_src}")

    with tempfile.TemporaryDirectory(prefix="ssd-keras-data-smoke-") as tmp:
        base = Path(tmp)
        if args.mode in {"csv", "all"}:
            smoke_csv(base / "csv")
        if args.mode in {"voc", "all"}:
            smoke_voc(base / "voc")
        if args.mode in {"coco", "all"}:
            smoke_coco(base / "coco")

    print("data-preparation smoke complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
