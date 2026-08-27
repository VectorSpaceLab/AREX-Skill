# Dummy Model Inventory

## Purpose

Read this when the model-integration flow needs a registry of the dummy models that the repo uses for initialization and smoke coverage.

## Inventory structure

`integration-test/models/inventory.json` is the default, small inventory used by the model-integration path. `integration-test/models/inventory-all.json` extends the set with every dummy model fixture that ships in the repo.

Each inventory entry contains fields such as:

- `id`: the model directory name under `integration-test/models/`.
- `task`: the model task name, such as classification, detection, embedding, or chat.
- `hardware`: the backend expectation recorded by the fixture; all entries in the current inventory are CPU fixtures.
- `version`: the dummy model version tag, usually `dev`.
- `configuration`: extra model settings when needed.

Each model directory normally contains:

- `README.md` with a short fixture description.
- `instill.yaml` with the model metadata.
- `model.py` with the dummy deployable implementation.

## Current dummy fixtures

| Model id | Task | Inventory file | Notes |
| --- | --- | --- | --- |
| `dummy-cls` | `TASK_CLASSIFICATION` | default inventory | Small classification fixture used by the default model-integration run. |
| `dummy-det` | `TASK_DETECTION` | inventory-all | Detection fixture. |
| `dummy-instance-segmentation` | `TASK_INSTANCE_SEGMENTATION` | inventory-all | Instance segmentation fixture. |
| `dummy-keypoint` | `TASK_KEYPOINT` | inventory-all | Keypoint fixture. |
| `dummy-semantic-segmentation` | `TASK_SEMANTIC_SEGMENTATION` | inventory-all | Semantic segmentation fixture. |
| `dummy-completion` | `TASK_COMPLETION` | inventory-all | Text completion fixture. |
| `dummy-chat` | `TASK_CHAT` | inventory-all | Chat fixture. |
| `dummy-text-to-image` | `TASK_TEXT_TO_IMAGE` | inventory-all | Text-to-image fixture. |
| `dummy-multimodal-chat` | `TASK_CHAT` | inventory-all | Multimodal chat fixture. |
| `dummy-text-embedding` | `TASK_EMBEDDING` | inventory-all | Text embedding fixture. |
| `dummy-multimodal-embedding` | `TASK_EMBEDDING` | inventory-all | Multimodal embedding fixture. |
| `dummy-ocr` | `TASK_OCR` | inventory-all | OCR fixture. |

## What to remember

- The model path uses the local registry plus the compose-dev stack to trigger model initialization.
- The `instill` CLI is required only for the build/push step; the dry-run helper can still inspect inventory structure without performing networked actions.
- `TASK_*` names come from `schema/ai-tasks.json` and the task schema files in `schema/`.
