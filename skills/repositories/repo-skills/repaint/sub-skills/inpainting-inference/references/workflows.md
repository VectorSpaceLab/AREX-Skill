# Inpainting workflows

## 1. Pick the right family

- **Face**: use a config in the face family when your images are aligned faces.
- **ImageNet**: use a config in the `test_inet256_*` family when you want the class-conditioned 256×256 model.
- **Places2**: use a config in the `test_p256_*` family for scene-like images.

## 2. Inspect the config before a heavy run

Run the bundled helper in dry-run mode first:

```bash
python scripts/run_inpainting.py \
  --conf_path path/to/your-face-config.yml \
  --dry_run
```

Check that the dry-run reports:

- a real checkpoint at `model_path`
- matching GT and mask counts
- the expected mask polarity and file order
- writable output paths under `paths.srs`, `paths.lrs`, `paths.gts`, and `paths.gt_keep_masks`

## 3. Run the sampler

After the dry-run is clean, omit `--dry_run`:

```bash
python scripts/run_inpainting.py \
  --conf_path path/to/your-face-config.yml
```

For a class-conditioned ImageNet-style run with a fixed label, pass `--cond_y`:

```bash
python scripts/run_inpainting.py \
  --conf_path path/to/imagenet-config.yml \
  --cond_y 207
```

The bundled helper is the public runtime entry point for this skill.

## 4. Inspect the outputs

The sample configs write to these directories:

- `inpainted` → final samples under `paths.srs`
- `gt_masked` → GT with the unknown region blanked out under `paths.lrs`
- `gt` → copied GT images, when `paths.gts` is set
- `gt_keep_mask` → saved keep masks under `paths.gt_keep_masks`

The filenames follow the GT basenames.

## 5. Adapt to custom images and masks

1. Copy the closest sample config.
2. Change `model_path`, `gt_path`, `mask_path`, and the `paths.*` outputs.
3. Keep `mask_loader: true`, `return_dict: true`, `return_dataloader: true`, and `random_crop: false`.
4. If you are using an ImageNet-style config, decide whether you want random labels or a fixed `cond_y`.
5. Dry-run again before the heavy run.

## 6. Leave schedule questions to the other sub-skill

If you want to tune `t_T`, `jump_length`, `jump_n_sample`, or `start_resampling`, switch to `../schedule-visualization/`.

## Practical signals

- `gt_path` / `mask_path` count mismatch → fix the layout before sampling.
- Mask appears inverted → invert the mask so known pixels are 255 and unknown pixels are 0.
- CPU run feels slow → that is expected; use dry-run first and only run the sampler when the layout is validated.
