# Custom Model Patterns

Read this when implementing or reviewing a custom Autodistill model class. The goal is to satisfy the core interface with the smallest deterministic checks before using expensive plugins or training targets.

## Custom Detection Base Model

A detection base model should store an ontology and return `supervision.Detections` from `predict`:

```python
import numpy as np
import supervision as sv
from autodistill.detection import CaptionOntology, DetectionBaseModel

class MyDetector(DetectionBaseModel):
    def __init__(self, ontology: CaptionOntology):
        self.ontology = ontology

    def predict(self, input):
        # Convert input as needed, run your model, then map results to class ids.
        return sv.Detections(
            xyxy=np.array([[10, 10, 100, 100]], dtype=float),
            confidence=np.array([0.9], dtype=float),
            class_id=np.array([0], dtype=int),
        )

ontology = CaptionOntology({"red widget": "widget"})
model = MyDetector(ontology)
model.label(input_folder="images", output_folder="dataset")
```

Conformance checklist:

- `self.ontology.classes()` order matches `class_id` values returned by `predict`.
- `predict` accepts at least the input type used by inherited `.label()`; detection labeling passes a cv2/Numpy image.
- Return confidence scores if the workflow uses `record_confidence=True`.
- Run the dataset-labeling dummy script or a tiny custom fixture before a large folder.

## Custom Classification Base Model

```python
import numpy as np
import supervision as sv
from autodistill.detection import CaptionOntology
from autodistill.classification import ClassificationBaseModel

class MyClassifier(ClassificationBaseModel):
    def __init__(self, ontology: CaptionOntology):
        self.ontology = ontology

    def predict(self, input: str) -> sv.Classifications:
        return sv.Classifications(
            class_id=np.array([0], dtype=int),
            confidence=np.array([0.95], dtype=float),
        )
```

Classification labeling writes train/test/valid class folders. Verify the exact `supervision.Classifications` structure supported by the installed `supervision` version and your target plugin.

## Custom Target Model

A target model consumes a labeled dataset and produces a trained/deployable model. Core abstract target classes do not define a universal training signature beyond `train`; concrete plugins choose arguments such as `dataset_yaml`, `epochs`, checkpoint paths, and output directories.

When writing a target plugin:

- Document the expected dataset layout.
- Validate required files before training.
- Keep `predict(input, confidence=...)` behavior consistent with the task type.
- Make training side effects explicit: output directory, checkpoints, GPU, and external services.

## Ontology Design

Use prompt names for base-model search language and class names for stable dataset labels:

```python
CaptionOntology({
    "forklift viewed from the side": "forklift",
    "warehouse pallet": "pallet",
})
```

Avoid changing class order after labeling because target model class ids depend on it. If two prompts should map to the same final class, test the concrete base model and target dataset writer carefully; duplicate class names can be confusing for downstream training.

## Interface Conformance Smoke

Run:

```bash
python scripts/check_interfaces.py
```

This validates core ontology behavior and dummy model conformance. Passing it does not prove a real plugin's weights, GPU path, or training loop.
