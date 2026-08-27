---
name: customization-extension
description: "Extend nnU-Net v2 with custom trainers, planners, preprocessors,
  normalization, image IO, label/region handling, external trainer deployment,
  and safe class discovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# nnU-Net v2 Customization and Extension

Use this sub-skill when the task is to change nnU-Net behavior by adding or selecting custom Python classes rather than only running standard workflows.

## Route here for

- Implementing or selecting custom `nnUNetTrainer` subclasses for loss, sampling, augmentation, optimizer, scheduler, checkpoint, or network changes.
- Making custom trainers portable for inference or continued training through checkpoint rename, `nnUNet_extTrainer`, editable source placement, or a fork.
- Implementing custom `ExperimentPlanner`, `DefaultPreprocessor` subclasses, resampling behavior, normalization classes, or image reader/writers.
- Understanding class discovery by name for trainers, planners, preprocessors, normalization schemes, label managers, and reader/writers.
- Diagnosing `trainer/planner/preprocessor/reader class not found`, external trainer import errors, or old custom trainer API signatures.
- Designing label/region/ignore-label behavior only when it affects custom code or extension compatibility.

## Do not handle here

- Dataset folder layout, `dataset.json` basics, file naming, and routine region/ignore-label authoring: use `data-preparation`.
- Running planning/preprocessing commands or deciding routine reruns: use `planning-preprocessing`.
- Routine training command matrices, folds, resume, validation, or selecting a built-in trainer by name: use `training-configuration`.
- Inference, ensembling, evaluation, pretrained model import/export, or model use: use `inference-evaluation`.

## Fast path

1. Identify the extension point and the class name nnU-Net will resolve: trainer, planner, preprocessor, normalization scheme, image reader/writer, label manager, or network architecture.
2. Prefer subclassing an existing nnU-Net implementation and overriding the smallest method needed.
3. If the extension changes preprocessing output, use a distinct plans name or `data_identifier` and rerun planning/preprocessing for affected configurations.
4. For custom trainers used outside the development environment, choose a sharing strategy before distributing checkpoints.
5. Before running expensive jobs, list available classes with the bundled read-only helper:
   ```bash
   python sub-skills/customization-extension/scripts/list_available_nnunet_classes.py --kind trainer
   ```
6. If a class is external, set `nnUNet_extTrainer` for trainer lookup or install/place source code so normal Python imports work.

## Bundled references

- `references/extension-points.md`: extension hook map, class names, plan fields, dataset metadata interactions, and discovery rules.
- `references/custom-trainers-and-sharing.md`: trainer subclass patterns and model-sharing choices for custom trainers.
- `references/troubleshooting.md`: lookup, import, API-signature, sharing, image IO, normalization, region, and ignore-label failures.

## Bundled helper

`list_available_nnunet_classes.py` imports nnU-Net and prints discovered class names without modifying files, checkpoints, plans, or environment variables. It can inspect built-in locations and optional external trainer roots:

```bash
python sub-skills/customization-extension/scripts/list_available_nnunet_classes.py --kind all
python sub-skills/customization-extension/scripts/list_available_nnunet_classes.py --kind trainer --external-trainer-dir /path/to/trainers
```
