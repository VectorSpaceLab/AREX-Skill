# Shared troubleshooting

These items apply across the RePaint sub-skills.
For inpainting-specific details, see `../sub-skills/inpainting-inference/references/troubleshooting.md`.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: blobfile` | runtime deps are incomplete in the active Python | use the verified inspection env or install the repo dependencies before running the sampler |
| `gt_path` / `mask_path` count mismatch | one directory has extra or missing images | make the pair counts equal; the loader asserts equal lengths |
| Wrong-looking inpainted region | mask polarity is reversed | ensure known pixels are `255` and unknown pixels are `0` before running |
| `random_crop` error | the shipped loader does not implement random crop | keep `random_crop: false` |
| `class_cond` loader error | the inpainting loader does not emit class labels | keep the eval loader's `class_cond: false` and use top-level `class_cond` only for the model |
| `cond_y` appears ignored | `class_cond` is false | only use `cond_y` with class-conditioned ImageNet-style configs |
| output directory permission error | the target output directory or one of its parents is not writable | point `paths.*` at a writable location |
| CPU inference is very slow | the model is large and the sampler is iterative | use the dry-run helper first; if you need speed tuning, move to schedule-visualization |
| `gt_keep_mask` missing in a custom wrapper | the batch dict dropped the keep-mask field | preserve `gt_keep_mask` so the sampler does not fall back to configuration-dependent behavior |

## Recovery pattern

1. Check the config with the bundled dry-run helper.
2. Confirm the checkpoint path and dataset/mask directories exist.
3. Verify mask polarity and pair counts.
4. Re-run the sampler only after the layout is clean.
