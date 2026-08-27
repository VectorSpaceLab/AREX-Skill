---
name: autodistill
description: "Guides core Autodistill workflows for foundation-model
  auto-labeling, target-model distillation, CLI/plugin registry use, custom
  model interfaces, and utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Autodistill Repo Skill

Use this skill when a task mentions Autodistill, automatic image labeling from foundation models, prompt-to-class ontologies, distilling labels into smaller vision target models, `autodistill` CLI commands, `DetectionBaseModel`/`CaptionOntology`, model plugin aliases, or Autodistill utility/debugging workflows.

Autodistill's core package defines interfaces, dataset writers, a CLI, a plugin registry, and utilities. Concrete base/target model implementations live in separate `autodistill-*` plugin packages and may require model downloads, GPU, credentials, long training, or separate licenses.

## First Steps

1. For stale-skill checks, read [repository provenance](references/repo-provenance.md).
2. For package concepts and snapshot caveats, read [package overview](references/package-overview.md).
3. Run the safe root smoke script when checking an environment:

```bash
python scripts/check_autodistill_install.py --check-cli
```

4. Route to the most specific sub-skill below.

## Sub-skill Routes

| User task | Read |
|---|---|
| Auto-label an image folder, validate a generated YOLO/classification dataset, debug `.label()`, use SAHI/NMS, or run a safe dummy dataset-writer check | [dataset-labeling](sub-skills/dataset-labeling/SKILL.md) |
| Build an `autodistill ...` command, inspect base/target aliases, understand plugin packages, run a safe CLI dry run, or debug CLI/model registry errors | [cli-and-model-registry](sub-skills/cli-and-model-registry/SKILL.md) |
| Design an ontology, implement a custom base/target model, validate abstract interface conformance, compose detector+classifier models, or use embedding ontologies | [ontologies-and-model-interfaces](sub-skills/ontologies-and-model-interfaces/SKILL.md) |
| Convert image inputs, use plotting/comparison helpers, split video frames, understand `split_data`, or handle Roboflow sync utility boundaries | [utilities](sub-skills/utilities/SKILL.md) |

## Install and Minimal Import Check

Core install:

```bash
pip install autodistill
python - <<'PY'
import autodistill
from autodistill.detection import CaptionOntology
print(autodistill.__version__)
print(CaptionOntology({"milk bottle": "bottle"}).classes())
PY
```

Plugin example for a full detection pipeline:

```bash
pip install autodistill autodistill-grounding-dino autodistill-yolov8
```

Install only the selected plugin packages. Do not install every supported model just to use the core package.

## Safe Core Workflow Skeleton

```python
from autodistill.detection import CaptionOntology
from autodistill_grounding_dino import GroundingDINO

ontology = CaptionOntology({"shipping container": "container"})
base_model = GroundingDINO(ontology=ontology)
base_model.label(input_folder="images", extension=".jpg", output_folder="dataset")
```

This shows the core call shape. The selected plugin's environment and runtime behavior must be verified separately.

## Cross-cutting Troubleshooting

Read [troubleshooting](references/troubleshooting.md) when failures involve install/import, missing plugins, GPU/backend crashes, CLI side effects, Roboflow credentials, dataset output, stale docs names, or utility boundaries.

Important snapshot warnings:

- Source-verified core version is `0.1.29`.
- In this snapshot the source method is `label()`, not the stale docs name `label_folder()`.
- In this snapshot the source method is `sahi_predict()`, not the stale docs name `predict_sahi()`.
- In this snapshot composed detection uses `ComposedDetectionModel`; some docs use stale names.
- The CLI `SUPPORTED_MODEL_TYPES` source constant has a missing comma, so classification/segmentation CLI paths may not match docs.

## Stop Conditions

Before continuing, ask for approval when a task would install plugin packages, download model weights, run large labeling/training, use GPU unexpectedly, contact Roboflow/cloud APIs, or overwrite user output directories.
