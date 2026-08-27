---
name: nnunet
description: "Guides the official PyTorch nnU-Net workflow for UNet++ training,
  inference, preprocessing, ensembling, pretrained models, and
  trainer/model-selection utilities."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# nnU-Net

Use this sub-skill for the repository's official PyTorch stack. It covers the
`nnunet` distribution, the `nnUNet_*` console scripts, and the official
UNet++ trainer/model variants built on nnU-Net.

## Route here when the user asks about

- `nnUNet_train`, `nnUNet_predict`, `nnUNet_plan_and_preprocess`,
  `nnUNet_convert_decathlon_task`, `nnUNet_ensemble`,
  `nnUNet_determine_postprocessing`, `nnUNet_find_best_configuration`,
  `nnUNet_download_pretrained_model`, `nnUNet_print_available_pretrained_models`,
  `nnUNet_print_pretrained_model_info`, `nnUNet_export_model_to_zip`,
  `nnUNet_install_pretrained_model_from_zip`, or `nnUNet_change_trainer_class`.
- Task-style dataset folders such as `Task003_Liver`.
- Path variables such as `nnUNet_raw_data_base`, `nnUNet_preprocessed`, or
  `RESULTS_FOLDER`.
- 3D training/inference, cascade workflows, model selection, or pretrained
  model sharing.

## What this sub-skill does

- Explains the expected data layout and environment variables for nnU-Net.
- Routes preprocessing, training, validation, inference, postprocessing,
  ensembling, and pretrained-model management.
- Helps diagnose version mismatches, missing imports, and stale advanced
  trainers.
- Provides a tiny runtime smoke script for safe inspection of the package,
  CUDA status, and sliding-window helpers.

## What to read first

- [`references/paths-and-environment.md`](references/paths-and-environment.md)
  for dataset folders, environment variables, and install assumptions.
- [`references/cli-reference.md`](references/cli-reference.md) for the public
  command set and important flags.
- [`references/workflows.md`](references/workflows.md) for end-to-end flows.
- [`references/pretrained-models.md`](references/pretrained-models.md) for the
  built-in pretrained model catalog and download/install cautions.
- [`references/troubleshooting.md`](references/troubleshooting.md) for common
  failure modes.
- [`references/api-reference.md`](references/api-reference.md) for important
  classes and functions used by the workflows.

## Recommended workflow order

1. Confirm the TaskXXX dataset layout and the three nnU-Net path variables.
2. Verify the installed `nnunet` package and CUDA support.
3. Run `nnUNet_plan_and_preprocess` only after the dataset root is sane.
4. Train with `nnUNet_train` or inspect with `nnUNet_predict`.
5. Use `nnUNet_determine_postprocessing`, `nnUNet_ensemble`, or
   `nnUNet_find_best_configuration` only after validation outputs exist.
6. Use pretrained-model helpers only when the user actually wants downloads,
   packaging, or inspection of available TaskXXX models.

## Important guardrails

- A CPU import does not prove the training path is ready. The verified runtime
  smoke should include CUDA status when the host provides a GPU.
- The inspected repo snapshot needed `batchgenerators==0.21` because newer
  releases no longer exposed `MultiThreadedAugmenter` from the import path used
  by nnU-Net.
- `matplotlib` is needed for some CLI imports, and `requests` is needed for the
  pretrained-model helpers.
- `nnUNet_change_trainer_class` is the public CLI name in this snapshot; the
  underlying module is `nnunet.inference.change_trainer`.
- `nnUNet_train_DP` and `nnUNet_train_DDP` are advanced multi-GPU entry points
  and should be treated cautiously if the installed source snapshot and runtime
  expectations drift.

## Bundled runtime helper

- [`scripts/check-nnunet-runtime.py`](scripts/check-nnunet-runtime.py) is a
  safe import / CLI / CUDA / sliding-window smoke helper. Use it when you need a
  quick confidence check without running a full dataset workflow.

## Common questions this sub-skill answers

- How should a TaskXXX dataset be arranged?
- Which environment variables must be set before planning or training?
- How do I list, inspect, download, export, or install pretrained nnU-Net
  models?
- Why does an nnU-Net CLI fail to import `matplotlib`, `requests`, or
  `MultiThreadedAugmenter`?
- How do I choose between `3d_lowres`, `3d_fullres`, and
  `3d_cascade_fullres`?
- How do I pick the right trainer or recover an old checkpoint's trainer name?

## Where to go next

- Use [`references/workflows.md`](references/workflows.md) for the concrete
  command sequences.
- Use [`references/troubleshooting.md`](references/troubleshooting.md) when the
  symptom is an import error, path error, data-layout problem, or advanced
  multi-GPU mismatch.
- Use the root [`../../SKILL.md`](../../SKILL.md) only if the user has not yet
  chosen between nnU-Net and the Keras stack.
