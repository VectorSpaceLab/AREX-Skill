---
name: developer-workflows
description: "Operate X-AnyLabeling developer workflows for training, packaging,
  localization, exporters, and contribution validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Developer Workflows

Use this sub-skill when the task is about X-AnyLabeling development rather than ordinary annotation use: Ultralytics training integration, training-worker diagnosis, PyInstaller build planning, translation/resource regeneration, ONNX exporter interpretation, contribution hygiene, or safe validation before an expensive local action.

## Route first

- Dataset format conversion details belong in `../conversion-cli/SKILL.md`.
- Loading an exported/custom model into the auto-labeling panel belongs in `../auto-labeling-models/SKILL.md`.
- Annotation UI, XLABEL JSON editing, and manual labeling workflows belong in `../annotation-ui/SKILL.md`.
- Release publishing and release-note generation are maintainer-only, side-effectful workflows; do not perform them from this sub-skill unless the user explicitly asks for release maintenance and provides the required release context.

## Capability map

| User intent | Use |
|---|---|
| Configure or diagnose GUI Ultralytics training | `references/training-workflows.md` and the bundled safe validator `scripts/check_training_config.py` |
| Inspect hidden training-worker payload/event behavior | `references/training-workflows.md` and `references/troubleshooting.md` |
| Plan a PyInstaller executable build | `references/packaging-and-localization.md` |
| Refresh translations or Qt resources | `references/packaging-and-localization.md` |
| Interpret selected ONNX exporter utility behavior | `references/model-exporters.md` |
| Prepare a contribution or focused developer check | `references/contributor-guidance.md` |
| Diagnose common failures | `references/troubleshooting.md` |

## Verified scope and safety limits

- Package identity used for this skill: `x-anylabeling-cvhub` version `4.0.2`, import package `anylabeling`, CLI entry point `xanylabeling`.
- Runtime baseline: Python `>=3.11` with Python `3.12` recommended. Optional package extras are `cpu`, `gpu`, `gpu-cu11`, and `gpu-cu13`; install only one runtime extra in a single environment.
- Adjacent verified routing facts: the conversion registry contained `19` tasks, and `ModelManager` loaded `204` configs after configuration initialization. Use the sibling conversion and auto-labeling sub-skills for those surfaces.
- ONNX Runtime CPU provider was verified during construction. CUDA, TensorRT, model downloads, and actual model training were not verified here and must be treated as optional local capabilities.
- Ultralytics training dependencies are optional. A normal annotation/runtime environment may not include `ultralytics` or a usable `torch` installation.
- The bundled validator only checks configuration shape and local device availability; it never launches training, downloads weights, writes datasets, or builds executables.

## Safe operating pattern

1. Classify the requested action as training, packaging/localization, exporter interpretation, or contribution hygiene.
2. Use the matching bundled reference to collect required fields and prerequisites.
3. For training requests, run the safe validator before launching anything expensive:

   ```bash
   python sub-skills/developer-workflows/scripts/check_training_config.py \
     --task-type Detect \
     --label-count 20 \
     --model yolov8n.pt \
     --data data.yaml \
     --project runs \
     --name exp \
     --device cpu
   ```

4. If validation passes but the task would train, build, mutate translations, or export a heavyweight model, tell the user what side effects will occur before proceeding.
5. Preserve license and dependency boundaries. Ultralytics is AGPL-3.0; using the training feature as a network service can carry source-disclosure obligations distinct from X-AnyLabeling's GPL-3.0-only project license.
