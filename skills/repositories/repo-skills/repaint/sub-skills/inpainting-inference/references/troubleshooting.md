# Inpainting troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `model_path does not exist` | the checkpoint path was copied from a template but not updated | point `model_path` at the real checkpoint file before running |
| `gt_path` / `mask_path` count mismatch | one directory has extra or missing images | fix the pair counts; the loader asserts equal lengths |
| Inpainted area looks like the known area or vice versa | mask polarity is reversed | invert the mask so known pixels are 255 and unknown pixels are 0 |
| Mask values are 0/1 or another non-255 scale | the mask was saved in a normalized or soft format | scale to 0/255 if you want a hard binary mask, or accept that the loader will treat it as soft weights |
| `random_crop` error | the shipped loader does not implement random crop | keep `random_crop: false` |
| `class_cond` error from the loader | the loader does not return class labels | keep the eval loader's `class_cond: false` and use top-level `class_cond` only for the model |
| `return_dict` error from the loader | the inpainting loader only implements dict outputs | keep `return_dict: true` so the sampler receives `GT`, `GT_name`, and `gt_keep_mask` |
| `cond_y` appears ignored | `class_cond` is false | only set `cond_y` for ImageNet-style class-conditioned configs |
| `use_ddim` error | this checkout does not expose a DDIM sampler | keep `use_ddim: false`; the bundled helper blocks it during dry-run |
| `gt_keep_mask` missing in a custom wrapper | the batch dict dropped the keep-mask field | preserve `gt_keep_mask`; the example inference path depends on it |
| output directory write failure | the output path or a parent directory is not writable | choose a writable location for `paths.srs`, `paths.lrs`, `paths.gts`, and `paths.gt_keep_masks` |
| CPU execution is very slow | the sampler is iterative and the model is large | use the dry-run helper first; if you need speed tuning, move to schedule-visualization |
| `ModuleNotFoundError: blobfile` | the active Python environment is missing the repo runtime deps | switch to the verified runtime env or install the missing dependency stack |

## Fast recovery pattern

1. Run the bundled helper with `--dry_run`.
2. Fix any count mismatch, missing path, or polarity warning.
3. Confirm the checkpoint and output directories are writable.
4. Re-run the sampler only after the layout is clean.

## Quick mask inversion example

If your masks use the opposite polarity, flip them before sampling:

```bash
python - <<'PY'
from pathlib import Path
from PIL import Image, ImageOps

mask_dir = Path("data/datasets/gt_keep_masks/my_masks")
for path in mask_dir.rglob("*.png"):
    image = Image.open(path).convert("L")
    ImageOps.invert(image).save(path)
PY
```
