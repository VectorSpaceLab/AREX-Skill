# Configuration and Model-Zoo Troubleshooting

Use this guide for read-only diagnosis before moving to training, testing, or inference execution.

## Quick Diagnosis Table

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `FileNotFoundError` or base config cannot load | Invalid `_base_` path or missing copied base files | Keep child config and its `_base_` tree together; inspect with `inspect_config.py --full`. |
| `ModuleNotFoundError: mmengine` | MMEngine missing | Install compatible OpenMMLab dependencies before using MMDetection configs. |
| `ModuleNotFoundError: mmcv._ext` | `mmcv-lite` installed or full MMCV ops unavailable | Install full `mmcv` compatible with PyTorch/CUDA; CPU still needs compiled ops for many detectors. |
| Registry/key errors for detector, transform, or dataset types | Wrong scope or custom module not registered | Ensure `default_scope='mmdet'`; reroute custom components to `customization-extension`. |
| `Can not find "auto_scale_lr"...` | `--auto-scale-lr` used on config missing required keys | Add/restore `auto_scale_lr = dict(enable=False, base_batch_size=...)` from the family schedule, then reroute training. |
| Checkpoint key mismatch | Config architecture differs from checkpoint | Pair checkpoint with the exact model-zoo config or deliberately handle missing/unexpected keys. |
| MIM config name not found | Using a file path, alias, or typo as a MIM model name | Look up `Name` in the model family's `metafile.yml`; avoid ambiguous aliases in automation. |
| Large download starts unexpectedly | Model-zoo helper downloaded weights | For config-only work, inspect local config files; ask before `mim download` or checkpoint retrieval. |

## Invalid `_base_`

MMEngine resolves `_base_` relative to the config file. Common breakages happen when a single config is copied without its `_base_` directory or when a hyphenated source config is translated into an underscore package config incorrectly.

Diagnosis:

```bash
python sub-skills/configuration-model-zoo/scripts/inspect_config.py CONFIG.py --full
```

Fixes:

- Copy the full dependent config tree, not only the leaf file.
- Preserve relative directory layout such as `configs/mask_rcnn/` beside `configs/_base_/`.
- If using installed-package configs, prefer the package's own config names/layout instead of mixing source-tree and package-tree paths.
- Do not edit `{{_base_.key}}` expressions unless replacing them with concrete values intentionally.

## Failed Config Import or Registry Scope

A config can load but later fail when building a model/dataset/transform because registries cannot find a class. For standard MMDetection components, the default scope should be `mmdet`. Some tools call `init_default_scope(cfg.get('default_scope', 'mmdet'))` before building.

Fixes:

- Add or preserve `default_scope = 'mmdet'` in standalone configs.
- Confirm MMDetection 3.3.0 and compatible MMEngine/MMCV are installed.
- If the type is custom, reroute to `customization-extension` so the module is registered before construction.

## Missing MMEngine or MMCV

MMDetection 3.x depends on MMEngine and MMCV. Full MMCV is required for many detection ops imports. Installing `mmcv-lite` can leave Python imports working until an op tries to import `mmcv._ext`, then fail.

Fixes:

- Use compatible OpenMMLab dependency installation for the environment.
- Prefer full `mmcv`, not `mmcv-lite`, for MMDetection workflows.
- If the system has no compatible compiled ops, limit work to pure config inspection and do not promise inference/training execution.

## Checkpoint and Config Incompatibility

Checkpoint/config mismatches usually appear as missing keys, unexpected keys, shape mismatches, wrong class counts, or poor predictions.

Check before execution:

- Model entry `Name`, `Config`, and `Weights` come from the same metafile entry.
- Architecture-defining fields are unchanged: `model.type`, backbone, neck channels, heads, class counts, and preprocessing.
- Task matches checkpoint: detection vs instance segmentation vs panoptic vs tracking.
- Dataset categories match the trained checkpoint if `num_classes` changed.

Safe stance: if the user changed architecture keys, treat model-zoo weights as incompatible until verified.

## `auto_scale_lr` Failures

Training script behavior requires all of these keys when enabling LR scaling:

```python
auto_scale_lr = dict(enable=False, base_batch_size=16)
```

Some configs inherit this from a schedule base such as `schedule_1x.py`; some common LSJ/SSJ configs use `base_batch_size=64`. Do not invent the number. Inspect the merged config, then preserve the family value.

Read-only check:

```bash
python sub-skills/configuration-model-zoo/scripts/inspect_config.py CONFIG.py --keys auto_scale_lr train_dataloader optim_wrapper
```

## Model Name vs Config Path Confusion

MIM commands expect model-zoo names such as `rtmdet_tiny_8xb32-300e_coco`; config-aware tools often expect a file path such as `configs/rtmdet/rtmdet_tiny_8xb32-300e_coco.py`.

Decision:

- If using `mim download mmdet --config ...`, pass a metafile `Name`.
- If using `Config.fromfile`, pass an actual readable config file path.
- If using high-level inferencer model aliases, confirm whether the API accepts aliases, local config paths, or both; do not assume every alias works everywhere.

## Safe CPU Planning Without Downloads

For a request like "choose RTMDet or Mask R-CNN for CPU inference" without permission to download checkpoints:

1. Choose a small model entry: `rtmdet_tiny_8xb32-300e_coco` for object detection or `mask-rcnn_r50_fpn_1x_coco` / `rtmdet-ins_tiny_8xb32-300e_coco` for masks.
2. Inspect config metadata only.
3. Hand off to `inference-visualization` with `device='cpu'` and a note that weights must be explicitly provided or downloaded.
4. Warn that CPU inference may be slow and full MMCV ops are still required.

## When to Stop and Reroute

- Need to run `tools/train.py`, `tools/test.py`, or launch distributed jobs: `training-testing`.
- Need to call `DetInferencer`, `init_detector`, or render predictions: `inference-visualization`.
- Need to define/register a new dataset, transform, module, or plugin import: `customization-extension`.
