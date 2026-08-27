# PySOT configuration reference

This reference covers PySOT experiment YAMLs and the merged global `cfg`. It is intended for editing and validation before routing to tracking, training, or evaluation workflows.

## Mental model

PySOT uses one global YACS configuration object named `cfg`. A YAML file is merged into the defaults, then `ModelBuilder()` and `build_tracker(model)` read the current global values. Config changes are therefore process-global; for reliable checks, run validation in a fresh Python process after each edit.

An inference config is normally enough to build the model graph and tracker. A training config adds `TRAIN` and `DATASET` sections and may contain pretrained backbone, batch-size, and learning-rate fields.

## Required top-level sections for an experiment YAML

The bundled validator treats a normal PySOT experiment YAML as incomplete unless these paths are present in the YAML file itself:

| Path | Purpose | Typical values or notes |
| --- | --- | --- |
| `META_ARC` | Human/model-zoo architecture label used by scripts and result naming. | Examples include `siamrpn_alex_dwxcorr`, `siamrpn_r50_l234_dwxcorr`, `siamrpn_mobilev2_l234_dwxcorr`. Do not rely on this alone; check `TRACK.TYPE` and `MASK.MASK`. |
| `BACKBONE.TYPE` | Backbone factory key. | `alexnetlegacy`, `alexnet`, `mobilenetv2`, `resnet18`, `resnet34`, `resnet50`. |
| `BACKBONE.KWARGS` | Backbone constructor arguments. | AlexNet uses `width_mult`; ResNet and MobileNet variants use `used_layers`. |
| `ADJUST.ADJUST` | Whether to add a neck/adjust layer after the backbone. | `false` for classic AlexNet SiamRPN; `true` for ResNet/MobileNet/SiamMask variants. |
| `ADJUST.TYPE` and `ADJUST.KWARGS` | Neck factory key and channels, required when `ADJUST.ADJUST: true`. | `AdjustLayer` or `AdjustAllLayer`; channel lists must align with selected backbone outputs. |
| `RPN.TYPE` | RPN head factory key. | `DepthwiseRPN`, `MultiRPN`, or `UPChannelRPN`. |
| `RPN.KWARGS.anchor_num` | Number of anchors used by RPN output channels. | Should equal `ANCHOR.ANCHOR_NUM`. |
| `MASK.MASK` | Enables SiamMask mask/refine modules. | `true` only for SiamMask-style configs. |
| `MASK.TYPE` and `MASK.KWARGS` | Mask head definition, required when `MASK.MASK: true`. | `MaskCorr`; common `out_channels` is `3969`. |
| `REFINE.REFINE` and `REFINE.TYPE` | Mask refinement module, required for `SiamMaskTracker`. | `Refine` when using SiamMask. |
| `ANCHOR.STRIDE` | Anchor stride in pixels. | Commonly `8`. |
| `ANCHOR.RATIOS` | Anchor aspect-ratio list. | Commonly `[0.33, 0.5, 1, 2, 3]`. |
| `ANCHOR.SCALES` | Anchor scale list. | Commonly `[8]`. |
| `ANCHOR.ANCHOR_NUM` | Explicit anchor count. | Must equal `len(RATIOS) * len(SCALES)`. |
| `TRACK.TYPE` | Tracker factory key used by `build_tracker`. | `SiamRPNTracker`, `SiamMaskTracker`, or `SiamRPNLTTracker`. |
| `TRACK.EXEMPLAR_SIZE` | Template crop size. | Commonly `127`. |
| `TRACK.INSTANCE_SIZE` | Search crop size used during tracking. | `255` for many ResNet/MobileNet configs, `287` for AlexNet SiamRPN. |
| `TRACK.BASE_SIZE` | Added score-grid base offset. | `8` for many ResNet/MobileNet configs, `0` for AlexNet SiamRPN. |
| `TRACK.CONTEXT_AMOUNT` | Context padding around target. | Commonly `0.5`. |

`TRAIN` and `DATASET` are optional for inference-only configs. When present, they add training-only constraints described below; route full training/data work to the training-data sub-skill.

## Common model-family signatures

Use this table to spot accidental cross-family edits. Values are distilled from the project configs and model-zoo naming.

| Family name | Backbone and layers | Neck/RPN | Mask? | Tracker | Typical use |
| --- | --- | --- | --- | --- | --- |
| `siamrpn_alex_dwxcorr` | `alexnetlegacy`, `width_mult: 1.0` | no adjust, `DepthwiseRPN(anchor_num=5, in_channels=256, out_channels=256)` | no | `SiamRPNTracker` | Fast short-term SiamRPN; tracker search size 287 and base size 0. |
| `siamrpn_alex_dwxcorr_otb` | same as AlexNet SiamRPN | same | no | `SiamRPNTracker` | OTB-tuned snapshot/config pairing. |
| `siamrpn_alex_dwxcorr_16gpu` | `alexnet`, `TRAIN_LAYERS: ['layer4', 'layer5']` | no adjust, `DepthwiseRPN` | no | `SiamRPNTracker` | Training recipe variant; includes `TRAIN`/`DATASET`. |
| `siamrpn_r50_l234_dwxcorr` | `resnet50`, `used_layers: [2, 3, 4]` | `AdjustAllLayer`, `MultiRPN`, usually weighted | no | `SiamRPNTracker` | ResNet-50 SiamRPN++ short-term model. |
| `siamrpn_r50_l234_dwxcorr_otb` | `resnet50`, `used_layers: [2, 3, 4]` | `AdjustAllLayer`, `MultiRPN(weighted: false)` | no | `SiamRPNTracker` | OTB-tuned ResNet model. |
| `siamrpn_mobilev2_l234_dwxcorr` | `mobilenetv2`, `used_layers: [3, 5, 7]`, `width_mult: 1.4` | `AdjustAllLayer`, `MultiRPN(weighted: false)` | no | `SiamRPNTracker` | Lighter model-zoo option. |
| `siammask_r50_l3` | `resnet50`, `used_layers: [0, 1, 2, 3]` | `AdjustAllLayer`, `DepthwiseRPN` | yes, `MaskCorr` + `Refine` | `SiamMaskTracker` | Segmentation/mask output. |
| `siamrpn_r50_l234_dwxcorr_lt` | `resnet50`, `used_layers: [2, 3, 4]` | `AdjustAllLayer`, `MultiRPN` | no | `SiamRPNLTTracker` | Long-term VOT-LT style tracking; see troubleshooting for legacy extra keys. |

Do not switch only the directory/model-zoo name or `META_ARC`. A valid model family requires a consistent `BACKBONE`, `ADJUST`, `RPN`, `MASK`/`REFINE`, `ANCHOR`, and `TRACK` block.

## Anchor and score-grid checks

### Anchor count

The core default sets:

```text
ANCHOR.ANCHOR_NUM = len(ANCHOR.RATIOS) * len(ANCHOR.SCALES)
```

For the common ratios `[0.33, 0.5, 1, 2, 3]` and scales `[8]`, the value is `5`. If you add a scale or remove a ratio, update both:

- `ANCHOR.ANCHOR_NUM`
- `RPN.KWARGS.anchor_num` when that key is present

A mismatch can cause incorrect RPN output channel counts, state-dict size mismatches, or tracker score/bbox conversion errors.

### Tracker score size

`SiamRPNTracker` and related trackers compute the score grid as:

```text
score_size = (TRACK.INSTANCE_SIZE - TRACK.EXEMPLAR_SIZE) // ANCHOR.STRIDE + 1 + TRACK.BASE_SIZE
```

Typical values:

- ResNet/MobileNet short-term config: `(255 - 127) // 8 + 1 + 8 = 25`.
- AlexNet SiamRPN config: `(287 - 127) // 8 + 1 + 0 = 21`.

Keep `INSTANCE_SIZE > EXEMPLAR_SIZE`, a positive `ANCHOR.STRIDE`, and a positive resulting score size. If `(INSTANCE_SIZE - EXEMPLAR_SIZE)` is not divisible by `STRIDE`, PySOT's tracker code floors the division; this may be intentional but deserves a warning when editing.

### Training output size

`TrkDataset` checks training configs with:

```text
desired_size = (TRAIN.SEARCH_SIZE - TRAIN.EXEMPLAR_SIZE) / ANCHOR.STRIDE + 1 + TRAIN.BASE_SIZE
```

and raises `size not match!` when `desired_size != TRAIN.OUTPUT_SIZE`.

Examples:

- Default ResNet-style training: `(255 - 127) / 8 + 1 + 8 = 25`, so `TRAIN.OUTPUT_SIZE` should be `25`.
- AlexNet 16-GPU training config: `(255 - 127) / 8 + 1 + 0 = 17`, so `TRAIN.OUTPUT_SIZE` should be `17`.

Only validate full dataset roots and annotations in the training-data sub-skill; this sub-skill validates the formula and model-side keys.

## Safe edit workflow

1. Copy the user-supplied config before editing.
2. Identify whether the edit is inference-only, training-only, or model-family-changing.
3. If changing model family, update these blocks together: `META_ARC`, `BACKBONE`, `ADJUST`, `RPN`, `MASK`, `REFINE`, `ANCHOR`, and `TRACK`.
4. If changing anchors, update `ANCHOR.ANCHOR_NUM` and any RPN `anchor_num` kwargs.
5. If enabling SiamMask, set `MASK.MASK: true`, configure `MASK.TYPE: MaskCorr`, enable `REFINE.REFINE: true`, and use `TRACK.TYPE: SiamMaskTracker`.
6. If using long-term tracking, use `TRACK.TYPE: SiamRPNLTTracker` and keep `TRACK.CONFIDENCE_LOW`, `TRACK.CONFIDENCE_HIGH`, and `TRACK.LOST_INSTANCE_SIZE` meaningful.
7. Run:

   ```bash
   python scripts/validate_config.py --config path/to/config.yaml
   ```

8. If the task asks for construction safety, run:

   ```bash
   python scripts/validate_config.py --config path/to/config.yaml --instantiate-model
   ```

9. Only after the config passes, route runtime execution to tracking-inference, training-data, or evaluation-toolkit as appropriate.

## What validation does not prove

- It does not prove a snapshot file exists or matches the model. Snapshot checks belong to tracking-inference, but this reference explains model-side mismatch symptoms.
- It does not prove CUDA benchmark, full training, or dataset availability.
- It does not prove historical paper/model-zoo metrics; those require the documented model snapshot, dataset, and evaluation setup.
