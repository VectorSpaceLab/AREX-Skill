# Autodistill Package Overview

Read this for the high-level operating model, core package boundaries, and plugin ecosystem assumptions.

## What Autodistill Does

Autodistill uses large foundation models to automatically label data, then trains smaller supervised target models on that labeled dataset. In the core vocabulary:

- **Base model:** a large model used for auto-labeling, such as Grounding DINO, Grounded SAM, CLIP-like classifiers, or cloud vision APIs.
- **Ontology:** the prompt/class mapping that tells a base model what to find and what labels to save.
- **Dataset:** the auto-labeled data produced by a base model.
- **Target model:** a smaller supervised model trained on that dataset.
- **Distilled model:** the trained model produced by the target package.

Autodistill 0.1.29 focuses on computer vision workflows, especially object detection and instance segmentation, with classification interfaces present but less uniformly supported.

## Core Package vs Plugins

The `autodistill` distribution provides:

- abstract base/target model interfaces;
- detection, classification, text-classification, and embedding ontology surfaces;
- dataset writing helpers;
- a CLI that orchestrates plugin imports;
- a model registry and model support matrix;
- image loading, plotting, comparison, video-frame, and Roboflow synchronization utilities.

Concrete model implementations are separate packages, commonly named like `autodistill-grounding-dino`, `autodistill-grounded-sam`, `autodistill-yolov8`, or `autodistill-clip`. Those plugin packages may require heavyweight ML frameworks, model downloads, CUDA/VRAM, cloud credentials, or their own licenses. Verify each plugin separately before full inference/training.

## Main Operating Routes

- Use [dataset labeling](../sub-skills/dataset-labeling/SKILL.md) to label image folders programmatically, validate output layouts, and run a safe core dataset-writer smoke.
- Use [CLI and model registry](../sub-skills/cli-and-model-registry/SKILL.md) to build CLI commands, inspect aliases, and avoid unintended plugin installs.
- Use [ontologies and model interfaces](../sub-skills/ontologies-and-model-interfaces/SKILL.md) to create custom base/target models, design ontologies, and compose detection/classification models.
- Use [utilities](../sub-skills/utilities/SKILL.md) for image conversion, plotting, comparison, video splitting, and Roboflow utility boundaries.

## Installation Baseline

For core package use:

```bash
pip install autodistill
python - <<'PY'
import autodistill
from autodistill.detection import CaptionOntology
print(autodistill.__version__)
print(CaptionOntology({"milk bottle": "bottle"}).classes())
PY
```

For a real end-to-end detection example, install only the selected plugins, for example:

```bash
pip install autodistill autodistill-grounding-dino autodistill-yolov8
```

Do not install every model plugin just to inspect the core package.

## Verified Snapshot Caveats

- Source version: `0.1.29`.
- The CLI's `SUPPORTED_MODEL_TYPES` constant has a missing comma, making the actual value `['detection', 'segmentationclassification']` in this snapshot.
- Some documentation examples use stale names such as `label_folder`, `predict_sahi`, `CustomDetectionModel`, or `CombinedDetectionModel`; source-verified core names include `.label()`, `.sahi_predict()`, and `ComposedDetectionModel`.
- The core package can be verified on CPU. Real plugin inference/training may require GPU or external credentials.
