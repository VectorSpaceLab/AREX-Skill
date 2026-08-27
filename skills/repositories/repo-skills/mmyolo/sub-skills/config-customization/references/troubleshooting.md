# Config Troubleshooting

Use this guide when an MMYOLO config fails to load, expands unexpectedly, has wrong dataset/classes, or is not ready for TTA. Do not run training, testing, deployment, downloads, or dataset conversion from this sub-skill.

## First diagnostic step

Run the bundled summary helper on the exact config and overrides the user plans to use:

```bash
python scripts/print_mmyolo_config_summary.py /path/to/config.py \
  --cfg-options key=value other.key=value
```

For a TTA request:

```bash
python scripts/print_mmyolo_config_summary.py /path/to/config.py --check-tta
```

Read the summary for:

- model/head `num_classes`
- assigner `num_classes`
- train/val/test dataset `metainfo`, `ann_file`, `data_prefix`, and pipeline types
- evaluator `ann_file`
- `max_epochs`, validation interval, checkpoint interval, logger interval, scheduler/hook epochs
- `tta_model`, `tta_pipeline`, and `batch_shapes_cfg`

## Config file cannot be loaded

Symptoms:

- `FileNotFoundError` for `_base_`.
- Python import or syntax error while loading the config.
- A relative path works from one location but not another.

Likely causes and fixes:

| Cause | Fix |
| --- | --- |
| `_base_` path is wrong after moving a child config | Keep child configs next to the family baseline when possible, or update `_base_` to the correct relative path from the child file. |
| Config was copied without its parent chain | Copy or recreate the full inherited structure, or make the child inherit a baseline available in the user's MMYOLO install/checkout. |
| Python syntax error in a config list/dict | Use the summary helper to trigger a parse-only failure; check brackets, commas, tuple commas such as `('cat', )`, and string quoting. |
| An override value contains spaces in a list/tuple | Quote list/tuple values and remove spaces inside the shell argument, for example `--cfg-options model.data_preprocessor.mean="[0,0,0]"`. |

## Wrong or missing classes

Symptoms:

- Model still reports 80 classes after editing a custom dataset.
- Evaluation labels or visualization labels are wrong.
- MMYOLO raises an assertion about metainfo keys.
- Fine-tuning from COCO reports head shape mismatch.

Checks and fixes:

1. Define lowercase metadata keys:

   ```python
   class_name = ('cat', )
   num_classes = len(class_name)
   metainfo = dict(classes=class_name, palette=[(20, 220, 60)])
   ```

2. Put `metainfo=metainfo` in train, val, and test dataset configs.
3. Set every family-required `num_classes` site:
   - YOLOv5/YOLOv7: `model.bbox_head.head_module.num_classes`; anchors if customized.
   - YOLOv6/PPYOLOE: head module plus `model.train_cfg.initial_assigner.num_classes` and `model.train_cfg.assigner.num_classes`.
   - YOLOv8/RTMDet: head module plus `model.train_cfg.assigner.num_classes`.
   - YOLOX: head module.
4. Ensure `palette` length is at least the number of classes.
5. Ensure class order matches the annotation category order.
6. Treat a pretrained checkpoint head mismatch as expected only when the class count changed and `load_from` is being used for initialization, not `resume`.
7. For one-class YOLOv5, a warning that classification loss is zero is expected.

## Dataset and evaluator annotation mismatch

Symptoms:

- Training uses one annotation file but validation/test metrics use another.
- Metrics are empty or unexpectedly `-1` for some scales.
- Test output is formatted for a different image set.

Checks:

```python
val_dataloader = dict(dataset=dict(
    data_root=data_root,
    ann_file='annotations/test.json',
    data_prefix=dict(img='images/')))
val_evaluator = dict(ann_file=data_root + 'annotations/test.json')
```

Fixes:

- Make `val_dataloader.dataset.ann_file` and `val_evaluator.ann_file` refer to the same validation annotation set unless intentionally different.
- Repeat the same check for `test_dataloader` and `test_evaluator`.
- Confirm `data_prefix=dict(img='...')` matches the image paths stored in the annotations.
- Metrics such as AP for small/medium objects can be `-1` when the dataset has no objects in that size range; this is not necessarily a config error.

Dataset layout validation and conversion belong to `data-tools`.

## Config inheritance did not override what you expected

Symptoms:

- An old component key remains after replacing a backbone/neck/head.
- A new `train_pipeline` is defined but the dataloader still uses the base pipeline.
- Changed `img_scale` does not affect validation/test transforms.

Fixes:

- Use `_delete_=True` when replacing a dict whose schema changed.
- Rebind intermediate variables into final fields:

  ```python
  train_dataloader = dict(dataset=dict(pipeline=train_pipeline))
  val_dataloader = dict(dataset=dict(pipeline=test_pipeline))
  test_dataloader = dict(dataset=dict(pipeline=test_pipeline))
  ```

- If changing normalization, update all relevant component dicts, usually backbone, neck, and sometimes head modules.
- Print the expanded summary after the edit; do not trust the child file alone.

## `--cfg-options` did not work

Symptoms:

- Override value is still a string when a list/bool/number was expected.
- List entry override touches the wrong field.
- Complex override is hard to review.

Fixes:

- Use dot paths through dicts: `model.bbox_head.head_module.num_classes=1`.
- Use integer list indexes only when the list structure is stable.
- Quote list/tuple values: `key="[1,2,3]"` with no whitespace inside the quoted value.
- Prefer a child config when editing metainfo, dataset roots, multiple class-count sites, anchors, pipelines, schedulers, hooks, or TTA.
- Re-run the summary helper with the exact `--cfg-options` to verify the expanded result.

## Shortened fine-tune schedule behaves strangely

Symptoms:

- Validation happens after training is effectively over.
- Last-stage mode switch or close-mosaic never happens.
- Warmup consumes too much of a tiny training run.
- Checkpoints/logs are too sparse or too frequent.

Fixes:

- Set `train_cfg.max_epochs` and `train_cfg.val_interval` together.
- Move `dynamic_intervals` switch points inside the new epoch range.
- Update family-specific custom hooks:
  - YOLOv6/YOLOX/PPYOLOE: last-epochs or mode-switch hook fields.
  - YOLOv8/RTMDet: close-mosaic/stage-2 switch epoch fields.
- Update scheduler list fields such as `begin`, `end`, and `T_max`.
- Update YOLO-specific param scheduler hook fields such as `max_epochs`, `warmup_mim_iter`, `warmup_min_iter`, `warmup_epochs`, or `total_epochs` when present.
- Align `default_hooks.checkpoint.interval` with validation interval and set `max_keep_ckpts` to bound disk use.

Training behavior validation belongs to `training-evaluation`; this sub-skill only checks that the config is internally coherent.

## TTA request fails

Symptoms:

- The test workflow asserts: cannot find `tta_model`.
- The test workflow asserts: cannot find `tta_pipeline`.
- TTA output shape behavior differs from non-TTA validation.

Checks and fixes:

1. The expanded config must contain both top-level variables:

   ```python
   tta_model = dict(type='mmdet.DetTTAModel', tta_cfg=dict(...))
   tta_pipeline = [dict(type='LoadImageFromFile'), dict(type='TestTimeAug', transforms=[...])]
   ```

2. If the family has a TTA base pattern, inherit or reproduce that pattern in the child config.
3. If only horizontal flip TTA is needed, edit `TestTimeAug.transforms` to remove the multiscale branch rather than passing a one-off override.
4. Expect MMYOLO test logic to set `test_dataloader.dataset.batch_shapes_cfg = None` during TTA. If the config relied on batch-shape padding, validate the TTA pipeline explicitly before handoff.
5. Use the helper with `--check-tta`; it exits nonzero if either required variable is missing.

## Deploy config confusion

Symptoms:

- User selects a config under a deploy family for training.
- User wants ONNX/TensorRT/RKNN export from this sub-skill.

Fix:

- Treat deploy configs as deployment backend configs, not model-training baselines.
- Route export, backend-specific config editing, TensorRT/RKNN/DeepStream, and converted artifact validation to `deployment-conversion`.
- This sub-skill may only confirm that the training/inference config selected for export has coherent model/dataloader/runtime fields.

## When to stop and route

Stop config editing and route when:

- A dataset path or annotation layout must be inspected or converted: `data-tools`.
- A model component, registry entry, or custom class must be implemented: `model-api`.
- A run command, checkpoint, metric output, or distributed launch must be executed: `training-evaluation`.
- An export/backend artifact must be created or validated: `deployment-conversion`.
