# Converters

Use the bundled checkpoint helper for **local, user-provided** files only. It does not download weights.

## Safe command shapes

Inspect first:

```bash
python scripts/checkpoint_tools.py inspect --checkpoint local/checkpoint.pth
```

Convert only after the family is known:

```bash
python scripts/checkpoint_tools.py convert \
  --family detr \
  --source-model local/source.pth \
  --output-model local/converted.pth
```

If the family is unclear, use `--family auto` and read the detection hints from the inspect output before writing anything.

## Conversion matrix

| Family mode | Main tensor patterns | Key remaps | Notes |
|---|---|---|---|
| `detr` | `backbone.0.body`, `encoder.layers`, `decoder`, `class_embed` | Backbone stem/res-stage rename; encoder and decoder attention/FFN rename; `level_embed` → `level_embeds`; `query_embed` → `query_embedding`; class-head index remap when the source head matches the DETR COCO shape | This is the simplest official DETR conversion path. |
| `deformable_detr` | `backbone.0.body`, `input_proj`, `encoder.layers`, `decoder`, `class_embed` | Backbone rename; `input_proj` → `neck.convs` / `neck.extra_convs`; encoder self-attention rename; decoder self/cross-attention rename; `level_embed` / `query_embed` rename; class-head remap when the head size matches the source COCO layout | Use for standard Deformable-DETR checkpoints. |
| `deformable_two_stage` | Same as `deformable_detr`, plus `class_embed.6` | Same as Deformable-DETR, but the special two-stage class head is truncated to the first 80 rows | Use only when the checkpoint really contains the two-stage head variant. |
| `conditional_detr` | `backbone.0.body`, `encoder.layers`, `decoder`, `label_enc`, `class_embed` | Backbone rename; conditional attention projections (`ca_*`, `sa_*`, `self_attn.out_proj`, `cross_attn.out_proj`); `decoder.norm` → `decoder.post_norm_layer`; `label_enc` → `label_encoder`; class-head remap when the source head matches the expected COCO shape | The label-encoder remap is specific to this family. |
| `dn_deformable_detr` | `backbone.0.body`, `input_proj`, `encoder.layers`, `decoder`, `class_embed` | Backbone rename; `input_proj` rename; conditional-style projection names; `decoder.norm` → `decoder.post_norm_layer`; `level_embed` → `level_embeds`; class-head remap when the source head matches the expected COCO shape | Similar to Conditional-DETR, but with deformable input projections. |

## What the helper does not do
- It does not fetch URLs.
- It does not run training or evaluation.
- It does not guess a project-specific trainer for DINO, MaskDINO, or CO-MOT.
- It does not convert already detrex-shaped checkpoints again.

## Family hints worth checking
- `label_enc` usually points to `conditional_detr`.
- `ca_` / `sa_` projection names usually point to `conditional_detr` or `dn_deformable_detr`.
- `input_proj` usually points to a Deformable-DETR family checkpoint.
- `class_embed.6` usually points to the special two-stage Deformable-DETR variant.
- `attentions.` and `decoder.post_norm_layer` often mean the checkpoint is already converted.
