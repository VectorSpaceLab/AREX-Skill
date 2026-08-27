# Dataset Labeling API Reference

Read this when you need exact method names, defaults, return objects, or enum values for Autodistill core labeling APIs. These facts are source- and installed-package-verified for Autodistill 0.1.29.

## Ontologies Used by Labeling

```python
from autodistill.detection import CaptionOntology

ontology = CaptionOntology({"milk bottle": "bottle", "bottle cap": "cap"})
ontology.prompts()  # ["milk bottle", "bottle cap"]
ontology.classes()  # ["bottle", "cap"]
ontology.promptToClass("milk bottle")  # "bottle"
ontology.classToPrompt("cap")  # "bottle cap"
```

`CaptionOntology({})` raises `ValueError("Ontology is empty")`. `promptToClass()` and `classToPrompt()` raise `ValueError` when the requested prompt or class is absent.

## `DetectionBaseModel`

```text
DetectionBaseModel.predict(self, input: str | numpy.ndarray | PIL.Image.Image) -> supervision.Detections
DetectionBaseModel.sahi_predict(self, input: str | numpy.ndarray | PIL.Image.Image) -> supervision.Detections
DetectionBaseModel.label(
    self,
    input_folder: str,
    extension: str = ".jpg",
    output_folder: str | None = None,
    human_in_the_loop: bool = False,
    roboflow_project: str | None = None,
    roboflow_tags: list[str] = ["autodistill"],
    sahi: bool = False,
    record_confidence: bool = False,
    nms_settings: NmsSetting = NmsSetting.NONE,
) -> supervision.DetectionDataset
```

Key behavior:

- `output_folder` defaults to `input_folder + "_labeled"`.
- Images are discovered with `glob(input_folder + "/*" + extension)`, so `.png` and `.jpeg` are ignored unless `extension` is changed.
- For every input path, `cv2.imread()` reads the image; if `sahi=True`, the model's prediction callback is wrapped by `supervision.InferenceSlicer`.
- `nms_settings` can apply class-specific or class-agnostic non-maximum suppression after prediction.
- A `supervision.DetectionDataset` is created using `self.ontology.classes()`, image paths, and detections.
- The dataset is exported through `dataset.as_yolo(...)`, then `autodistill.helpers.split_data(...)` creates train/valid layout.
- `record_confidence=True` writes `confidence-<image>.txt` files and requires `detections.confidence` to be present.
- `human_in_the_loop=True` calls Roboflow login/upload paths and needs network credentials.

## `NmsSetting`

```python
from autodistill.detection.detection_base_model import NmsSetting

NmsSetting.NONE            # "no_nms"
NmsSetting.CLASS_SPECIFIC  # "class_specific"
NmsSetting.CLASS_AGNOSTIC  # "class_agnostic"
```

Use `CLASS_SPECIFIC` to call `detections.with_nms()` and `CLASS_AGNOSTIC` to call `detections.with_nms(class_agnostic=True)`.

## `ClassificationBaseModel`

```text
ClassificationBaseModel.predict(self, input: str) -> supervision.Classifications
ClassificationBaseModel.label(
    self,
    input_folder: str,
    extension: str = ".jpg",
    output_folder: str | None = None,
) -> supervision.ClassificationDataset
```

Key behavior:

- `output_folder` defaults to `input_folder + "_labeled"`.
- Images are discovered with the same extension filter as detection labeling.
- Predictions are collected into a `supervision.ClassificationDataset` with `self.ontology.classes()`.
- The dataset is split 70/15/15 into train/test/valid and written as folder structures.

Classification support is part of the core interfaces, but many concrete classification base/target behaviors depend on plugin packages.

## Target Model Interfaces

The core package defines abstract targets but does not train a model by itself:

```text
DetectionTargetModel.predict(self, input: str, confidence: float = 0.5) -> supervision.Detections
DetectionTargetModel.train(self)
ClassificationTargetModel.predict(self, input: str, confidence: float = 0.5) -> supervision.Classifications
ClassificationTargetModel.train(self)
```

Concrete target packages such as YOLOv8 implement their own constructor, `train`, and `predict` details. Verify the plugin package before assuming epochs, checkpoint names, data paths, GPU behavior, or output directories.
