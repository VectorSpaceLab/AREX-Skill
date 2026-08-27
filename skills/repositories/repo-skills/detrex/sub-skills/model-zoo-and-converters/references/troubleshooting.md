# Troubleshooting

## First response checklist
1. Run `inspect` on the checkpoint.
2. Check whether the key prefixes look like the expected family.
3. Confirm whether the checkpoint is already detrex-shaped.
4. Only then run a bounded local conversion.

## Common failures

| Symptom | Likely cause | What to do |
|---|---|---|
| The helper refuses a path or says downloads are disabled | A URL or remote weight was provided | Download the file outside this skill, then point the helper at the local checkpoint. |
| The inspect output shows `attentions.` or `decoder.post_norm_layer` already | The checkpoint is probably already converted | Do not reconvert it; load it directly or inspect it as a detrex checkpoint. |
| You see missing or unexpected class-head keys | Wrong family mode, wrong dataset head, or the source head size does not match the remap rule | Re-run inspect, confirm the family, and use the matching converter mode. For the Deformable two-stage variant, use the special `deformable_two_stage` path. |
| `input_proj` keys are present but the rest of the layout does not match | The checkpoint may be from a Deformable-DETR family but not the exact one you chose | Compare the presence of `cross_attn`, `ca_*`, `sa_*`, and `label_enc` against the converter matrix. |
| The backbone shape does not match the neck | Wrong backbone depth, DC5 setting, or pretrained feature wrapper | Re-check `freeze_at`, `res5_dilation`, `out_indices`, or `return_nodes`. |
| A DINO config trains poorly when evaluated with the default trainer | The model row actually expects the hacked DINO trainer | Switch to the DINO project route instead of the generic trainer path. |
| A MaskDINO checkpoint loads but boxes or masks look wrong | The box-init mode or hidden-dimension variant does not match the checkpoint | Revisit `INITIALIZE_BOX_TYPE` and make sure the config matches the checkpoint shape. |
| CO-MOT routing is unclear | The project is tracking-first, not a plain detector | Use the CO-MOT project notes; do not assume a released DINO-backbone route exists yet. |

## Good signs
- `class_embed` was remapped only when its source shape matched the expected family.
- `label_enc` was renamed to `label_encoder` only for Conditional-DETR.
- `input_proj` was rewritten into `neck.convs` or `neck.extra_convs` only for the Deformable-style families.
- The inspect report says the checkpoint already looks detrex-shaped.

## If you are still unsure
Stop at inspect mode and hand the key summary to the next step. For this sub-skill, the safe failure mode is “do not convert yet.”
