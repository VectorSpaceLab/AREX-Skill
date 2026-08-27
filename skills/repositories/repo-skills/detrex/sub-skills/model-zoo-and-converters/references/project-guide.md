# Project guide

This sub-skill covers the detrex families that show up in the model zoo and the checkpoint conversion paths that are safe to automate locally.

## Fast selection rule
- **Converted weights**: already in detrex keyspace; load them directly.
- **Hacked trainer**: use the project-specific trainer because the optimizer grouping or learning-rate split is different from the default detrex loop.
- **Special backbone or mask init**: keep the matching project config; do not swap backbone families casually.
- **Official foreign checkpoint**: inspect first, then convert only with the matching family.

## Family and route matrix

| Family | When to choose it | Trainer/config signal | Notes |
|---|---|---|---|
| DETR | You are converting or evaluating an official DETR checkpoint | Standard detrex DETR config plus the local converter helper | The converter remaps backbone, encoder, decoder, and COCO class-head keys. |
| Deformable-DETR | You need box-refinement or two-stage Deformable-DETR weights | Standard detrex Deformable-DETR config | The family includes a special two-stage variant with a different class-head shape. |
| Conditional-DETR | You have an official Conditional-DETR checkpoint or a detrex config that expects the conditional attention layout | Standard detrex Conditional-DETR config | This family adds the conditional query/key projection names and a label-encoder remap. |
| DN-Deformable-DETR | You have an official DN-Deformable-DETR checkpoint | Standard detrex DN-Deformable-DETR config | Similar to Conditional-DETR style projections, plus deformable input-projection remaps. |
| DINO | You need DINO baselines or DINO backbone variants | Use the DINO project route when the row says **hacked trainer** or when optimizer grouping matters | DINO spans ResNet, Swin, FocalNet, ViT, ConvNeXt, InternImage, and EVA variants. |
| MaskDINO | You need detection plus segmentation, or mask-enhanced box initialization | MaskDINO project configs | The mask-init setting is part of the model contract; see the backbone and troubleshooting notes before reusing a checkpoint. |
| CO-MOT | You need multi-object tracking or DanceTrack-style workflows | CO-MOT project configs and trainer | The project README marks DINO backbone support as TODO, so do not promise a released DINO-backbone route. |

## What the model zoo labels mean
- **converted**: the checkpoint was adapted from an official upstream repo into detrex naming and tensor layout.
- **hacked trainer**: detrex uses a project-specific training loop with different optimizer groups or learning rates.
- **with EMA / AMP**: these are training-policy variants, not a different family.
- **backbone-specific rows**: the backbone family matters as much as the detector family; keep the config aligned with the published row.

## Practical routing notes
- For **DINO**, use the project trainer when you want the stronger detrex baseline. The project README says the hacked trainer aligns optimizer parameters with Deformable-DETR-style grouping.
- For **MaskDINO**, keep the `INITIALIZE_BOX_TYPE` choice in mind: `no`, `mask2box`, or `bitmask` all change how decoder boxes are initialized.
- For **CO-MOT**, treat the tracking configs as project-specific, not plain detection configs. The helper here should only inspect or route checkpoints, not invent a new MOT pipeline.
- For **official DETR-family weights**, use the local checkpoint helper and the matching family. Do not mix families just because the backbone is the same.

## Recommended workflow
1. Inspect the checkpoint with the bundled helper.
2. Compare the observed key signals against the table above.
3. If the model zoo row says converted, skip conversion and load it directly.
4. If the row says hacked trainer, use the matching project trainer route instead of the default one.
5. If the checkpoint is an upstream DETR-family file, convert it only with the matching family mode.
