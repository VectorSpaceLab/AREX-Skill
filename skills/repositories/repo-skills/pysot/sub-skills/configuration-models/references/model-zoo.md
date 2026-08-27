# PySOT model-zoo naming and selection

This reference distills the model-zoo naming conventions and benchmark-column meanings needed for config/model tasks. It does not provide or require model downloads; tracking workflows must validate user-supplied snapshots separately.

## Name grammar

Most model-zoo names follow this pattern:

```text
<architecture>_<backbone-or-family>[_layers]_<xcorr>[_benchmark-or-training-suffix]
```

Examples:

| Name | Meaning |
| --- | --- |
| `siamrpn_alex_dwxcorr` | SiamRPN tracker, AlexNet backbone, depth-wise cross-correlation. |
| `siamrpn_alex_dwxcorr_otb` | AlexNet SiamRPN tuned/reported for OTB. |
| `siamrpn_r50_l234_dwxcorr` | SiamRPN++ style model with ResNet-50 features from layers 2, 3, and 4. |
| `siamrpn_r50_l234_dwxcorr_otb` | ResNet-50 l234 SiamRPN tuned/reported for OTB. |
| `siamrpn_mobilev2_l234_dwxcorr` | SiamRPN with MobileNetV2 multi-layer features. |
| `siammask_r50_l3` | SiamMask model with ResNet-50 feature usage for mask-capable tracking. |
| `siamrpn_r50_l234_dwxcorr_lt` | Long-term SiamRPN tracker configuration for VOT-LT-style use. |
| `*_8gpu` or `*_16gpu` configs | Training recipe variants; do not assume they are separate inference model-zoo rows unless the snapshot naming explicitly says so. |

## Tokens and suffixes

| Token | Interpretation |
| --- | --- |
| `siamrpn` | Siamese Region Proposal Network tracker producing bounding boxes. |
| `siammask` | SiamMask model that can produce masks/polygons in addition to boxes. |
| `alex` | AlexNet backbone family. In inference configs this often maps to `BACKBONE.TYPE: alexnetlegacy`. |
| `r50` | ResNet-50 backbone. In configs this maps to `BACKBONE.TYPE: resnet50`. |
| `mobilev2` | MobileNetV2 backbone. |
| `l234` | Uses multiple backbone outputs, commonly layers 2, 3, and 4 for ResNet-50 or corresponding MobileNetV2 feature indices. |
| `l3` | SiamMask naming shorthand; inspect the YAML's `BACKBONE.KWARGS.used_layers` instead of inferring all channels from the name. |
| `dwxcorr` | Depth-wise cross-correlation, the SiamRPN++ style correlation head. |
| `_otb` | OTB-tuned/reported variant. Pair it with an OTB snapshot/config when reproducing OTB metrics. |
| `_lt` | Long-term tracking variant, expected to use `SiamRPNLTTracker` and long-term confidence/search-size keys. |

## Benchmark columns in the model zoo

| Column family | Meaning | Owned by |
| --- | --- | --- |
| `VOT16/18/19 (EAO/A/R)` | VOT short-term expected average overlap, accuracy, and robustness. | Metric interpretation and result layout route to evaluation-toolkit. |
| `OTB2015 (AUC/Prec.)` | OTB success AUC and precision. | Evaluation-toolkit for metrics; this sub-skill only maps suffixes/configs. |
| `VOT18-LT (F1)` | Long-term tracking F1 score. | Evaluation-toolkit for metric details. |
| `Speed (fps)` | Reported inference speed, tested on GTX-1080Ti in the source model-zoo note. | Treat as historical guidance, not a guarantee for a user's hardware. |

A dash means the model-zoo table did not report that metric for that row.

## Choosing a model/config family

Use this decision guide for config/model tasks:

- Need fastest simple bounding-box tracking: start from `siamrpn_alex_dwxcorr`; expect lower accuracy but high reported speed.
- Need stronger short-term accuracy and can afford a heavier model: start from `siamrpn_r50_l234_dwxcorr`.
- Need a lighter multi-layer modern backbone: consider `siamrpn_mobilev2_l234_dwxcorr`.
- Need segmentation mask or polygon output: use `siammask_r50_l3` and keep `MASK.MASK`, `REFINE.REFINE`, and `TRACK.TYPE: SiamMaskTracker` consistent.
- Need VOT long-term behavior: use `siamrpn_r50_l234_dwxcorr_lt` and confirm `TRACK.TYPE: SiamRPNLTTracker` plus long-term confidence keys.
- Need OTB reproduction: choose an `_otb` config/snapshot pair instead of changing only `META_ARC`.
- Need training from scratch/fine-tuning: `_8gpu`/`_16gpu` configs are training recipes; route dataset and distributed-launch details to training-data.

## Snapshot pairing rules

A model-zoo row implies both a config and a snapshot. For safe operation:

1. Select the model-zoo family.
2. Use the matching config family.
3. Validate the config with `scripts/validate_config.py`.
4. In tracking-inference, validate that the snapshot exists and load it only after the config/model graph matches.

Do not mix an OTB snapshot with a non-OTB config, a SiamMask snapshot with a SiamRPN config, or an AlexNet snapshot with a ResNet/MobileNet config unless the user intentionally trained/exported that combination.

## Config-name traps

- `META_ARC` is a label, not the only source of truth. The SiamMask config's `META_ARC` may look like a SiamRPN label; rely on `MASK.MASK`, `REFINE.REFINE`, and `TRACK.TYPE` for behavior.
- Config strings use implementation factory keys (`resnet50`, `alexnetlegacy`) rather than the short model-zoo tokens (`r50`, `alex`).
- Long-term configs may carry legacy extra YAML keys that the base YACS defaults reject; see [troubleshooting.md](troubleshooting.md) before editing or validating an LT config.
