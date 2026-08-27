---
name: ontologies-and-model-interfaces
description: "Guides custom Autodistill ontologies, base/target model
  interfaces, composed detection, and embedding workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Autodistill Ontologies and Model Interfaces

Use this sub-skill when a task asks how to design an ontology, implement a custom base or target model, check interface conformance, compose detection and classification models, or reason about embedding/text-classification surfaces.

Autodistill core classes define contracts; concrete model behavior normally lives in plugin packages. If the task is only to label a folder using an existing plugin, start with [dataset labeling](../dataset-labeling/SKILL.md). If the task is to pick a CLI alias or inspect installed plugins, start with [CLI and model registry](../cli-and-model-registry/SKILL.md).

## Quick Route

- **Exact signatures and abstract methods:** read [API reference](references/api-reference.md).
- **Build a custom base/target model:** read [custom model patterns](references/custom-model-patterns.md) for class skeletons, return objects, and conformance checks.
- **Combine detection and classification or use embeddings:** read [composed and embedding workflows](references/composed-and-embedding-workflows.md) for actual source class names and caveats.
- **Debug interface errors:** read [troubleshooting](references/troubleshooting.md) for abstract class instantiation, missing methods, ontology map errors, stale docs names, temp-file side effects, and set-of-marks limits.
- **Run safe conformance checks:** use [scripts/check_interfaces.py](scripts/check_interfaces.py). It constructs dummy models and validates core ontology/interface behavior without plugins.

## Core Pattern

A base model maps user data plus an ontology to predictions or labeled datasets:

```python
from autodistill.detection import CaptionOntology, DetectionBaseModel

class MyDetector(DetectionBaseModel):
    def __init__(self, ontology: CaptionOntology):
        self.ontology = ontology

    def predict(self, input):
        # return supervision.Detections
        ...
```

The inherited `DetectionBaseModel.label()` method will call `predict()` for every selected image and write the detection dataset. Use [dataset labeling](../dataset-labeling/SKILL.md) to validate the output layout.

## Ontology Design Rules

- Prompts are what the base model sees.
- Classes are what the dataset and target model will save.
- Keep class names stable before training; changing class order or labels changes target model semantics.
- `CaptionOntology` rejects empty mappings and raises lookup errors for missing prompts/classes.

## Snapshot Caveats

- Public docs mention `CustomDetectionModel` or `CombinedDetectionModel` in some composition examples. In this source snapshot, the available class is `autodistill.core.composed_detection_model.ComposedDetectionModel`.
- `TextClassificationBaseModel.label(...)` is a stub (`pass`) in this snapshot; do not claim it writes a dataset without a plugin override.
- Some embedding ontology methods and docs have implementation caveats; inspect and test with the concrete embedding model before large labeling jobs.
