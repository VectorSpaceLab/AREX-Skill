# Data and Configuration Troubleshooting

## `FileNotFoundError` for list-mode images

**Symptom:** the loader tries to open a path such as `<dataset>/./00002.jpg` and fails.

**Likely cause:** a list file contains entries relative to `trainA`, but the config points `data_folder_train_a` to the dataset parent instead of the `trainA` folder.

**Fix:** either set `data_folder_train_a` to the folder containing the listed images, or rewrite list entries to include the split folder prefix. Run:

```bash
python scripts/inspect_munit_dataset.py --config /path/to/config.yaml --repo-root /path/to/user/munit-checkout
```

## `Found 0 images in: ...`

**Symptom:** `ImageFolder` raises a runtime error naming a split folder.

**Likely causes:** missing split directory, unsupported extension, archive not extracted, crop/split step wrote to the wrong folder, or config path is relative to a different working directory.

**Fix:** inspect the folder tree, verify extensions are in the supported image extension set, and prefer absolute `data_root` while debugging.

## Missing `trainA`, `trainB`, `testA`, or `testB`

Folder mode requires all four. For a one-off demo, create a tiny split with at least `display_size` images per split or lower `display_size` in the config.

## `display_size` index errors

Training indexes the first `display_size` samples from all four train/test datasets before the loop starts. If any split has fewer images, reduce `display_size` or add images to the split.

## Crop or resize issues

If images are smaller than `crop_image_height` or `crop_image_width`, random crop can fail. Either resize up first through `new_size`/`new_size_a`/`new_size_b`, lower the crop size, or prepare images at the intended resolution.

## `yaml.load` warnings or errors

The original helper uses `yaml.load(stream)` without a Loader. Modern PyYAML may warn or fail. The bundled validators use a safe loader when available; if the original code fails in a modern environment, route to `../environment-and-setup/` or `../model-internals/` for a porting plan.

## UNIT selected with a MUNIT config

`--trainer UNIT` needs `recon_kl_w` and `recon_kl_cyc_w`. The bundled MUNIT configs do not include those keys. Add UNIT-specific loss weights and review model semantics in `../model-internals/` before running.

## Demo scripts are too destructive

If a user asks to run a demo script, split the request into explicit steps: approve download, choose a scratch dataset directory, run crop/extract commands in that scratch area, validate the resulting folder layout, and only then route to `../training/` for command construction.
