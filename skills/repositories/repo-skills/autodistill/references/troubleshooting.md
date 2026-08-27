# Autodistill Troubleshooting

Read this for cross-cutting failures that affect the core package, plugin ecosystem, CLI, and generated skill routing.

## Install and Import

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: autodistill` | Core package is not installed in the active Python | Install `autodistill` in the environment that will run the workflow; run `scripts/check_autodistill_install.py`. |
| Import error for `cv2`, `supervision`, `PIL`, `yaml`, `click` | Core runtime dependency missing or environment mismatch | Reinstall the core package or its requirements in the active environment; run `python -m pip check`. |
| Import error for `autodistill_grounding_dino`, `autodistill_yolov8`, etc. | Concrete model plugin is separate from the core package | Install only the selected plugin package and verify it independently. |
| Plugin import crashes inside torch/CUDA/framework code | Plugin-specific backend/wheel/driver mismatch | Prepare the plugin's backend environment; do not treat a core CPU import as proof of plugin GPU readiness. |

## CLI and Registry

- Validate commands with [CLI troubleshooting](../sub-skills/cli-and-model-registry/references/troubleshooting.md) before running full labeling/training.
- Avoid `-y true` unless the user approves plugin installation side effects.
- Use explicit boolean values for boolean options in this snapshot.
- Treat `--upload-to-roboflow true` as credentialed and externally mutating.

## Dataset Labeling

- Use [dataset troubleshooting](../sub-skills/dataset-labeling/references/troubleshooting.md) for empty folders, extension mismatches, `record_confidence`, SAHI/NMS, memory pressure, and output layout checks.
- Run the bundled tiny dataset script to separate core dataset-writer problems from plugin inference problems.

## Interface and Ontology

- Use [interface troubleshooting](../sub-skills/ontologies-and-model-interfaces/references/troubleshooting.md) for abstract methods, ontology errors, stale docs class names, composed-model temp files, and embedding caveats.
- Confirm `class_id` values align with `ontology.classes()` before writing labels.

## Utility Boundaries

- Use [utility troubleshooting](../sub-skills/utilities/references/troubleshooting.md) for `load_image`, plotting, video splitting, and Roboflow sync helpers.
- Avoid URL/network utility branches in deterministic tests unless explicitly approved.

## When to Stop and Ask

Stop for explicit approval before:

- installing model plugins or broad dependency groups;
- downloading weights or datasets;
- running long training or benchmark-scale labeling;
- using GPU/accelerator resources that were not already selected;
- logging into or uploading to Roboflow/cloud services;
- overwriting a user's dataset or model output directory.
