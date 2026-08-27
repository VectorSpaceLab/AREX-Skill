# Object Detection with MultiModalPredictor

Use this reference for `problem_type="object_detection"`. Detection has stricter data/backend requirements than ordinary text/image classification.

## Minimal API Pattern

```python
from autogluon.multimodal import MultiModalPredictor

predictor = MultiModalPredictor(
    problem_type="object_detection",
    sample_data_path=train_data,  # COCO JSON path or detection DataFrame
    hyperparameters={
        "model.mmdet_image.checkpoint_name": "yolov3_mobilenetv2_8xb24-320-300e_coco",
        "model.mmdet_image.output_bbox_format": "xyxy",
        "env.num_gpus": 0,
    },
)

predictor.fit(train_data, time_limit=1200)
metrics = predictor.evaluate(test_data)
predictions = predictor.predict(test_data, as_pandas=True)
```

`sample_data_path` helps infer object categories/classes. If class inference fails, pass `num_classes` and/or `classes` in the constructor.

## COCO Annotation Expectations

A COCO detection annotation JSON should contain:

```json
{
  "images": [{"id": 1, "file_name": "JPEGImages/000001.jpg", "width": 640, "height": 480}],
  "annotations": [{"id": 1, "image_id": 1, "category_id": 1, "bbox": [10, 20, 100, 80], "area": 8000, "iscrowd": 0}],
  "categories": [{"id": 1, "name": "object"}]
}
```

Checks:

- `images[*].id` values must be unique and referenced by annotations.
- `images[*].file_name` should resolve relative to the JSON file location or the supplied image root.
- `categories[*].id` values must cover all annotation `category_id` values.
- COCO `bbox` is `[x, y, width, height]`; AutoGluon prediction output may be configured as `xyxy` or `xywh` through `model.mmdet_image.output_bbox_format`.
- A prediction-only COCO file may contain `images` without `annotations`, but training/evaluation needs annotations.

Use the bundled validator:

```bash
python scripts/inspect_multimodal_inputs.py --coco annotations/train.json --image-root . --check-images
```

## VOC-Style Dataset Expectations

VOC-style datasets usually have:

```text
VOC_ROOT/
  Annotations/*.xml
  JPEGImages/*.jpg
  ImageSets/Main/*.txt
```

The repository provides a VOC-to-COCO conversion CLI in the package, but future agents should not depend on the source checkout. If conversion is needed in a user environment with AutoGluon installed, use the installed module entry point and user-provided local data:

```bash
python -m autogluon.multimodal.cli.voc2coco --root_dir VOC_ROOT
```

Conversion expectations distilled from the source:

- XML objects provide class names and bounding boxes.
- `labels.txt` can be generated from annotations to map classes to 1-based IDs.
- Invalid boxes where `xmin >= xmax`, `ymin >= ymax`, or area is too small are skipped.
- Output COCO files are written under the annotation directory for discovered splits.

Validate VOC metadata before conversion:

```bash
python scripts/inspect_multimodal_inputs.py --voc-root VOC_ROOT --check-images
```

## DataFrame Detection Format

AutoGluon utilities can convert COCO/VOC annotations into a DataFrame. A detection DataFrame typically contains:

- `image`: local image path.
- `rois`: a list/array of bounding boxes and class labels.
- `label`: often a copy of `rois` for training.

A row-level RoI value follows the pattern:

```python
[[x1, y1, x2, y2, class_label], ...]
```

Use a DataFrame when annotations are generated programmatically or already loaded. Keep `image` and `label`/`rois` aligned row-by-row.

## Inference Inputs

Detection inference can accept several shapes when the backend is available:

```python
predictor.predict("image.jpg")
predictor.predict(["image1.jpg", "image2.jpg"])
predictor.predict({"image": ["image1.jpg", "image2.jpg"]})
predictor.predict(test_df[["image"]])
predictor.predict("annotations/test_images_only.json", save_results=True)
```

`save_results=True` is detection-specific and may write COCO or CSV-style results depending on kwargs. Use explicit output directories when exposing this in an application.

## Class Metadata

Class metadata can come from:

- COCO `categories` in `sample_data_path`.
- A detection DataFrame generated from annotation files.
- Explicit `num_classes` and `classes` constructor arguments.

Failure to provide class metadata commonly appears as shape mismatch in the detection head, unknown category IDs, or empty metric results.

## Backend Notes

Object detection often needs optional packages beyond base AutoGluon multimodal:

- MMDetection/MMCV-compatible stack for `mmdet_image` models.
- `pycocotools` or `torchmetrics` for evaluation.
- GPU-compatible PyTorch/torchvision builds for practical training, although CPU imports can work with matching CPU wheels.

If the user has only CPU and no optional detection stack, provide data validation and code structure but be explicit that real detection training/inference may not run until backends are installed.

## Troubleshooting Checklist

- `problem_type` must be exactly `object_detection`.
- `train_data` should be a COCO JSON path or a detection DataFrame, not a plain image folder.
- `sample_data_path` should point at a representative annotated split or DataFrame.
- COCO category IDs must match annotation `category_id` values.
- Image paths referenced in JSON must resolve locally.
- Empty annotations, invalid boxes, and class names absent from metadata will break or degrade training.
- `env.num_gpus=-1` auto-selects available GPU; set `env.num_gpus=0` for CPU-only validation examples.
- Torch/torchvision/MMCV/MMDetection version mismatches are common; run `scripts/multimodal_smoke.py --optional-backends` before diagnosing model code.
