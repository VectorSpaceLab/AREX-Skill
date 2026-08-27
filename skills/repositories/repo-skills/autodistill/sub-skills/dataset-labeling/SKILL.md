---
name: dataset-labeling
description: "Guides Autodistill dataset auto-labeling workflows, output
  layouts, and safe dummy verification for detection and classification base
  models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Autodistill Dataset Labeling

Use this sub-skill when a task asks how to auto-label image folders, inspect or validate Autodistill dataset output, choose `CaptionOntology` prompts/classes for labeling, use SAHI/NMS during labeling, or debug core `.label()` behavior without running a real foundation model.

Autodistill's core package supplies base-model interfaces and dataset writers. Real foundation models such as Grounding DINO, Grounded SAM, CLIP, YOLOv8, or cloud plugins live in separate `autodistill-*` packages and may require downloads, credentials, GPU, or long training. For plugin aliases and CLI orchestration, read [the CLI and model registry sub-skill](../cli-and-model-registry/SKILL.md). For implementing a custom model class, read [ontologies and model interfaces](../ontologies-and-model-interfaces/SKILL.md).

## Quick Route

- **Programmatic image auto-labeling:** read [workflows](references/workflows.md) for `.label()` patterns, ontology setup, SAHI/NMS switches, and Roboflow upload boundaries.
- **Detection/classification output layout:** read [data formats](references/data-formats.md) before validating `data.yaml`, YOLO labels, train/valid splits, or classification folders.
- **Signatures and defaults:** read [API reference](references/api-reference.md) for source-verified method names, parameters, return types, and enum values.
- **Problems while labeling:** read [troubleshooting](references/troubleshooting.md) for empty inputs, extension mismatches, missing confidence values, memory pressure, plugin/backend failures, and credentialed Roboflow paths.
- **Safe local proof of core dataset writing:** run [scripts/create_tiny_detection_dataset.py](scripts/create_tiny_detection_dataset.py) to create a tiny deterministic YOLO-style detection dataset without any model plugin.

## Core Concepts

1. Build an ontology, usually `CaptionOntology({"prompt sent to base model": "saved class name"})`.
2. Instantiate a base model plugin or a custom subclass whose task matches the dataset you want.
3. Call `base_model.label(input_folder=..., extension=".jpg", output_folder=...)`.
4. Validate the generated dataset layout before handing it to a target model plugin.

In this source snapshot the verified source method is `label()`. Some public docs mention `label_folder()`; treat that as a stale alias unless a concrete plugin adds it. The verified SAHI method on `DetectionBaseModel` is `sahi_predict()`, while `.label(..., sahi=True)` uses `supervision.InferenceSlicer` internally.

## Minimal Programmatic Pattern

```python
from autodistill.detection import CaptionOntology
from autodistill_grounding_dino import GroundingDINO

ontology = CaptionOntology({"milk bottle": "bottle", "bottle cap": "cap"})
base_model = GroundingDINO(ontology=ontology)
base_model.label(input_folder="images", extension=".jpg", output_folder="dataset")
```

This pattern proves the core call shape. The plugin package, model weights, hardware, and optional training target must be selected and verified separately.

## Validation Checklist

- `ontology.classes()` contains exactly the labels expected by the target model.
- The `input_folder` contains files matching `extension`; default is `.jpg` only.
- Detection outputs contain `confidence` if `record_confidence=True`.
- The generated detection dataset has `data.yaml`, train/valid image folders, and train/valid label folders.
- Any full model run has explicit approval for downloads, credentials, GPU, or long training.

## Safe Smoke Script

Run the bundled dummy script after installing `autodistill` and `supervision`:

```bash
python scripts/create_tiny_detection_dataset.py --keep
```

It uses a deterministic in-process `DetectionBaseModel` subclass, creates two tiny images, calls the inherited `label()` implementation, and checks the output layout. Passing this script means the core dataset writer works; it does **not** verify any external base-model plugin.
