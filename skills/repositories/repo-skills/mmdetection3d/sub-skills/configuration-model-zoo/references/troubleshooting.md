# Configuration and Model-Zoo Troubleshooting

Use this when config inspection, selection, or adaptation fails before execution. For failures during dataset conversion, training/evaluation, inference, visualization, or custom module implementation, route to the owning sub-skill after isolating the config symptom.

## `mmengine` is missing

Symptom: [`../scripts/check_config.py`](../scripts/check_config.py) exits with an error that MMEngine could not be imported.

Action:

1. Do not parse MMDetection3D configs as plain text if inheritance matters.
2. Use an environment with the MMDetection3D/OpenMMLab runtime installed.
3. Re-run the inspector from a directory where the candidate config and its relative `_base_` files are available.

## Config file cannot resolve `_base_`

Symptoms: file-not-found errors for inherited config files, or a child config parses only when run from one directory.

Action:

- Pass a config path whose relative base files exist next to it, or run from the config tree that contains the base hierarchy.
- Do not copy a child config alone without its base chain unless you flatten it first with a config printer/inspector.
- If making a standalone config is required, inspect the fully merged config and then create a deliberate standalone file; do not guess inherited defaults.

## Registry or scope errors

Symptoms: build-time errors such as an unknown detector, dataset, transform, loss, metric, visualizer, or hook type.

Action:

- Confirm the parsed config has `default_scope = 'mmdet3d'` unless the config intentionally uses a different OpenMMLab scope.
- Keep scope-prefixed names, such as `mmdet.*`, when a component comes from another OpenMMLab package.
- If the type belongs to an optional project, route import and dependency setup to `customization-extensions`.
- If parsing succeeds but building fails, the issue is usually registry import/dependency setup rather than config syntax.

## `--cfg-options` appears ignored

Causes and fixes:

- Wrong key path: inspect the merged config first and use the actual v1.x key, such as `train_dataloader.batch_size`, not an old `data.*` path unless the parsed config really has `data`.
- List indexing: use numeric indexes for pipeline steps, for example `.pipeline.0.type`.
- Shell quoting: quote list/tuple values as one shell token, for example `model.data_preprocessor.mean="[127,127,127]"`.
- Coordinated edits: use a child config instead of many CLI overrides when class names, pipelines, evaluator, and model heads must change together.

## Old loader fields conflict with new dataloader fields

Symptoms: compatibility assertions involving `samples_per_gpu`, `workers_per_gpu`, `persistent_workers`, or `imgs_per_gpu`.

Action:

- Prefer top-level `train_dataloader`, `val_dataloader`, and `test_dataloader` fields in v1.x configs.
- Do not set both old global loader fields and new per-dataloader fields.
- Replace deprecated `imgs_per_gpu` with the appropriate dataloader batch setting.
- When adapting a legacy config, inspect after compatibility conversion before launching execution.

## Dataset root changed but training/test still fails

Likely causes:

- The raw dataset was not converted to MMDetection3D info files.
- `ann_file`, `data_prefix`, object-sampling database paths, or evaluator annotation files still point to old filenames.
- The dataset is wrapped, so the override changed an outer wrapper rather than the inner dataset.
- The train and test pipelines still expect different point dimensions, sweeps, image fields, or calibration fields.

Action: route raw layout/conversion work to `data-preparation`; then re-inspect the config and update all coupled dataset/evaluator fields.

## Class-count or class-order mismatch

Symptoms: checkpoint load shape mismatch, evaluator class mismatch, impossible metrics, or predictions with swapped labels.

Action:

- Match `metainfo.classes`, dataset class order, model head `num_classes`, anchor/class-specific sampler settings, and evaluator assumptions.
- For a checkpoint, use the same class set and order as the config used to train it unless intentionally fine-tuning with a changed head.
- Be careful with old nuImages artifacts because older conversion behavior affected class ordering; reconvert and select a config/checkpoint from the same convention.

## Model/checkpoint pair mismatch

Symptoms: missing/unexpected state-dict keys, tensor size mismatch, low accuracy, or an alias that only partially matches a config.

Action:

- Compare the full basename tokens: algorithm, backbone/neck/head, voxel or backend setting, dataset, class count, schedule, AMP/TTA markers.
- Prefer the checkpoint linked from the same row/family as the config.
- Treat `load_from` as pretrained initialization and `resume=True` as resuming optimizer/runner state; do not use `resume` for a mismatched checkpoint.
- If only a checkpoint URL is available, infer the intended config from the checkpoint basename before running inference or evaluation.

## Sparse backend or CUDA extension missing

Symptoms: errors importing or building sparse convolution components, PAConv CUDA variants, or backend-specific segmentation models.

Action:

- Inspect the config name and model fields for backend tokens such as `torchsparse`, `minkowski`, `spconv`, or CUDA-specific variants.
- Select a CPU-compatible/non-CUDA variant only if the family actually provides one and the user accepts the capability difference.
- Route backend installation and custom extension checks to root environment guidance or `customization-extensions`; do not claim a sparse model is runnable from config parsing alone.

## Project config imports fail

Symptoms: config parsing or model building references a project module that is not imported.

Action:

- Identify whether the requested family is a project extension such as BEVFusion, CenterFormer, TR3D, DETR3D, PETR, or TPVFormer.
- Keep config selection in this sub-skill, but route project import wiring, optional dependencies, and custom registry setup to `customization-extensions`.
- After project setup is verified, re-run config inspection before handoff to training/evaluation or inference.

## Model-zoo row has no checkpoint

Causes:

- Some datasets or rows provide logs but no released pretrained weights because of licensing or release status.
- Some rows are ablation rows such as “above w/o circle NMS” and do not have a separate config/checkpoint link.

Action:

- State that the row is useful as a training/evaluation reference but cannot be used for pretrained inference unless a compatible checkpoint is supplied.
- For evaluation-only reproduction, route to `training-evaluation` only after data and config are available.

## TTA or evaluator output is wrong

Symptoms: TTA flags change nothing, output files are missing, or submission formatting is not generated.

Action:

- Check both the test pipeline and the model `test_cfg`; TTA can require changes in both places.
- Check `test_evaluator` for `format_only`, `submission_prefix`, or result output fields.
- Route command construction and output handling to `training-evaluation` after the config fields are confirmed.
