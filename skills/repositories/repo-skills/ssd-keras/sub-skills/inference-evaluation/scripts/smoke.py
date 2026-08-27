#!/usr/bin/env python3
from __future__ import annotations

import argparse
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


def make_image(path: Path, size: tuple[int, int] = (300, 300)) -> None:
    image = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    image[80:220, 80:220] = [80, 180, 80]
    Image.fromarray(image).save(path)


def make_voc_dataset(base: Path) -> tuple[Path, Path, Path]:
    base.mkdir(parents=True, exist_ok=True)
    images_dir = base / "voc_images"
    annotations_dir = base / "voc_annotations"
    images_dir.mkdir()
    annotations_dir.mkdir()
    image_name = "sample.jpg"
    make_image(images_dir / image_name)

    image_set_file = base / "voc_test.txt"
    image_set_file.write_text("sample\n")

    annotation = Element("annotation")
    SubElement(annotation, "folder").text = "voc_images"
    SubElement(annotation, "filename").text = image_name
    size = SubElement(annotation, "size")
    SubElement(size, "width").text = "300"
    SubElement(size, "height").text = "300"
    SubElement(size, "depth").text = "3"
    obj = SubElement(annotation, "object")
    SubElement(obj, "name").text = "cat"
    SubElement(obj, "pose").text = "Unspecified"
    SubElement(obj, "truncated").text = "0"
    SubElement(obj, "difficult").text = "0"
    bbox = SubElement(obj, "bndbox")
    SubElement(bbox, "xmin").text = "80"
    SubElement(bbox, "ymin").text = "80"
    SubElement(bbox, "xmax").text = "220"
    SubElement(bbox, "ymax").text = "220"
    ElementTree(annotation).write(annotations_dir / "sample.xml")
    return images_dir, image_set_file, annotations_dir


def make_coco_dataset(base: Path) -> tuple[Path, Path]:
    base.mkdir(parents=True, exist_ok=True)
    images_dir = base / "coco_images"
    images_dir.mkdir()
    image_name = "sample.jpg"
    make_image(images_dir / image_name)
    annotations_path = base / "coco.json"
    coco = {
        "images": [
            {"id": 1, "file_name": image_name, "width": 300, "height": 300},
        ],
        "annotations": [
            {
                "id": 1,
                "image_id": 1,
                "category_id": 1,
                "bbox": [80, 80, 140, 140],
                "area": 19600,
                "iscrowd": 0,
            }
        ],
        "categories": [
            {"id": 1, "name": "cat"},
        ],
    }
    annotations_path.write_text(json.dumps(coco))
    return images_dir, annotations_path


def make_decoded_prediction() -> np.ndarray:
    return np.array([[[1.0, 0.99, 80.0, 80.0, 220.0, 220.0]]], dtype=np.float32)


def decode_smoke() -> None:
    from ssd_encoder_decoder.ssd_output_decoder import decode_detections, decode_detections_fast
    for package_name in ["ssd_encoder_decoder", "bounding_box_utils"]:
        assert_bundled_module(package_name)

    raw = np.array(
        [
            [
                [
                    0.01,
                    0.99,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.5,
                    0.5,
                    0.4,
                    0.4,
                    0.1,
                    0.1,
                    0.2,
                    0.2,
                ]
            ]
        ],
        dtype=np.float32,
    )
    decoded = decode_detections(
        raw,
        confidence_thresh=0.5,
        iou_threshold=0.45,
        top_k=10,
        input_coords="centroids",
        normalize_coords=True,
        img_height=300,
        img_width=300,
    )
    decoded_fast = decode_detections_fast(
        raw,
        confidence_thresh=0.5,
        iou_threshold=0.45,
        top_k=10,
        input_coords="centroids",
        normalize_coords=True,
        img_height=300,
        img_width=300,
    )
    print(f"decode_detections: {decoded[0].shape}")
    print(f"decode_detections_fast: {decoded_fast[0].shape}")


def evaluation_smoke(base: Path) -> None:
    from data_generator.object_detection_2d_data_generator import DataGenerator
    from data_generator.object_detection_2d_geometric_ops import Resize
    from data_generator.object_detection_2d_misc_utils import apply_inverse_transforms
    from data_generator.object_detection_2d_photometric_ops import ConvertTo3Channels
    from eval_utils.average_precision_evaluator import Evaluator
    for package_name in ["data_generator", "eval_utils", "ssd_encoder_decoder", "bounding_box_utils"]:
        assert_bundled_module(package_name)

    images_dir, image_set_file, annotations_dir = make_voc_dataset(base / "voc")
    dataset = DataGenerator(load_images_into_memory=False)
    dataset.parse_xml(
        images_dirs=[str(images_dir)],
        image_set_filenames=[str(image_set_file)],
        annotations_dirs=[str(annotations_dir)],
        classes=["background", "cat"],
    )

    class FakeModel:
        def predict(self, batch_X):
            return make_decoded_prediction().repeat(len(batch_X), axis=0)

    evaluator = Evaluator(model=FakeModel(), n_classes=1, data_generator=dataset, model_mode="inference")
    mAP = evaluator(
        img_height=300,
        img_width=300,
        batch_size=1,
        data_generator_mode="resize",
        average_precision_mode="sample",
        num_recall_points=11,
        ignore_neutral_boxes=True,
        return_precisions=False,
        return_recalls=False,
        return_average_precisions=False,
        verbose=False,
    )
    print(f"VOC mAP: {mAP}")

    generator = dataset.generate(
        batch_size=1,
        shuffle=False,
        transformations=[ConvertTo3Channels(), Resize(height=300, width=300)],
        returns={"processed_images", "inverse_transform", "image_ids"},
        keep_images_without_gt=True,
    )
    batch_X, image_ids, inverse_transforms = next(generator)
    _ = apply_inverse_transforms([make_decoded_prediction()[0]], inverse_transforms)
    print(f"inverse-transform batch: {batch_X.shape}, {len(image_ids)} images")


def coco_export_smoke(base: Path) -> None:
    from data_generator.object_detection_2d_data_generator import DataGenerator
    from eval_utils.coco_utils import get_coco_category_maps, predict_all_to_json
    for package_name in ["data_generator", "eval_utils"]:
        assert_bundled_module(package_name)

    images_dir, annotations_path = make_coco_dataset(base / "coco")
    dataset = DataGenerator(load_images_into_memory=False)
    dataset.parse_json(
        images_dirs=[str(images_dir)],
        annotations_filenames=[str(annotations_path)],
        ground_truth_available=True,
    )
    _, classes_to_cats, _, classes_to_names = get_coco_category_maps(str(annotations_path))

    class FakeModel:
        def predict(self, batch_X):
            return make_decoded_prediction().repeat(len(batch_X), axis=0)

    results_path = base / "results.json"
    predict_all_to_json(
        out_file=str(results_path),
        model=FakeModel(),
        img_height=300,
        img_width=300,
        classes_to_cats=classes_to_cats,
        data_generator=dataset,
        batch_size=1,
        data_generator_mode="resize",
        model_mode="inference",
        confidence_thresh=0.01,
        iou_threshold=0.45,
        top_k=200,
        pred_coords="centroids",
        normalize_coords=True,
    )
    results = json.loads(results_path.read_text())
    print(f"COCO mapping classes: {classes_to_names}")
    print(f"COCO export rows: {len(results)}")


def graph_smoke() -> None:
    from models.keras_ssd7 import build_model
    for package_name in ["models", "keras_layers", "bounding_box_utils"]:
        assert_bundled_module(package_name)

    model = build_model(image_size=(300, 300, 3), n_classes=1, mode="inference")
    y_pred = model.predict(np.zeros((1, 300, 300, 3), dtype=np.float32))
    print(f"graph prediction: {y_pred.shape}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Synthetic inference / evaluation smoke for the bundled SSD Keras skill.")
    parser.add_argument(
        "--skip-graph",
        action="store_true",
        help="Skip the built-in inference graph smoke and run only the NumPy / evaluator checks.",
    )
    args = parser.parse_args()

    skill_root, runtime_src = add_runtime_source()
    print(f"skill-root: {skill_root}")
    print(f"runtime-source: {runtime_src}")

    if not args.skip_graph:
        graph_smoke()
    decode_smoke()

    with tempfile.TemporaryDirectory(prefix="ssd-keras-inference-smoke-") as tmp:
        base = Path(tmp)
        evaluation_smoke(base)
        coco_export_smoke(base)

    print("inference-evaluation smoke complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
