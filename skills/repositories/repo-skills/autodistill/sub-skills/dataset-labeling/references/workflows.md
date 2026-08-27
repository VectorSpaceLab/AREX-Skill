# Dataset Labeling Workflows

Read this for concrete Autodistill labeling patterns. These workflows use the core package APIs and clearly mark where plugin-specific packages, downloads, GPU, or credentials enter.

## Workflow: Label Images with a Base Model Plugin

```python
from autodistill.detection import CaptionOntology
from autodistill_grounding_dino import GroundingDINO

ontology = CaptionOntology({
    "shipping container": "container",
    "container door": "door",
})
base_model = GroundingDINO(ontology=ontology)

dataset = base_model.label(
    input_folder="images",
    extension=".jpg",
    output_folder="dataset",
)
```

Validation:

1. Confirm `ontology.classes()` gives the exact class names expected by the target model.
2. Confirm `dataset/data.yaml` exists and names those classes.
3. Confirm at least one image and label moved into `dataset/train` or `dataset/valid`.
4. Inspect a few labels or visualize predictions before training.

Plugin note: `GroundingDINO` is not included in the core package. Install and verify the plugin package separately.

## Workflow: Use NMS or SAHI During Detection Labeling

```python
from autodistill.detection.detection_base_model import NmsSetting

base_model.label(
    input_folder="images",
    output_folder="dataset",
    sahi=True,
    nms_settings=NmsSetting.CLASS_AGNOSTIC,
)
```

Use SAHI for small objects when the concrete plugin's `predict` can run on image slices. Expect slower inference. Use NMS when overlapping predictions need filtering. If the plugin already applies NMS internally, compare results before enabling another NMS pass.

For a single image, the source method name is:

```python
detections = base_model.sahi_predict("image.jpg")
```

Some docs mention `predict_sahi`; verify the plugin before using that spelling.

## Workflow: Record Confidence Values

```python
base_model.label(
    input_folder="images",
    output_folder="dataset",
    record_confidence=True,
)
```

This writes `confidence-<image-stem>.txt` files next to YOLO labels. It requires `supervision.Detections.confidence` to be non-null. If your custom base model omits confidence, either add confidence scores or leave `record_confidence=False`.

## Workflow: Label Classification Data

```python
from autodistill.detection import CaptionOntology
from some_autodistill_classification_plugin import SomeClassifier

ontology = CaptionOntology({"red widget": "red", "blue widget": "blue"})
base_model = SomeClassifier(ontology=ontology)
base_model.label(input_folder="images", extension=".jpg", output_folder="classified")
```

The core classification base class writes train/test/valid class folders. Concrete plugin support varies; check the plugin's package and docs before assuming confidence thresholds, target model compatibility, or GPU needs.

## Workflow: Human-in-the-loop Roboflow Upload

```python
base_model.label(
    input_folder="images",
    output_folder="dataset",
    human_in_the_loop=True,
    roboflow_project="my-project",
)
```

This calls Roboflow login/upload flows. Do not run it as a dry run. It needs network, account credentials, and a clear destination project decision.

## Workflow: Safe Core Writer Check Without Plugins

Run the bundled script:

```bash
python scripts/create_tiny_detection_dataset.py --keep
```

Use this when you need to distinguish a broken Autodistill core installation from a broken plugin/model download. If the script passes but a real base model fails, debug the plugin package, model weights, hardware, or input data rather than the core dataset writer.
