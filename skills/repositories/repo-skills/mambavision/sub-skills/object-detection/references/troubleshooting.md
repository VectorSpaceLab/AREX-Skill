# Troubleshooting

Use this file for MambaVision object-detection problems that involve MMDetection, MMCV, MMEngine, MMSEG, COCO layout, registry imports, or checkpoint compatibility.

## OpenMMLab version mismatch or mmcv build failure

Symptoms:

- `ImportError` or `undefined symbol` when importing `mmcv`, `mmdet`, `mmseg`, or `mmpretrain`
- `MMCV` wheel fails to install or imports a different ABI than the installed PyTorch build
- `<openmmlab-train-entrypoint> --help` fails before argument parsing

Actions:

1. Verify the installed package versions match the pinned stack from `references/configuration.md`.
2. Check the PyTorch CUDA build and the installed `mmcv` wheel are built for compatible CUDA/torch versions.
3. Reinstall the OpenMMLab stack in a clean environment if the import surface is mixed from different installs.
4. Confirm `python - <<'PY'` import smoke for `mmengine`, `mmcv`, `mmdet`, `mmseg`, and `mmpretrain` before debugging the model.

If `mmcv` built from source, make sure the build saw the same PyTorch that your runtime uses.

## `MM_mamba_vision` is not in the registry

Symptoms:

- `KeyError: MM_mamba_vision is not in the MODELS registry`
- the config file parses, but model construction fails before training starts
- `<openmmlab-train-entrypoint>` or `<openmmlab-test-entrypoint>` works only after manual imports

Actions:

1. Make sure the target project's adapter directory is importable before building the runner.
2. If you are inside a notebook or a custom launcher, import the adapter module first:

   ```python
   import mamba_vision
   ```

3. Check that `mamba_vision` is imported before the runner builds the config.
4. If you invoke from elsewhere, add the `tools` directory to `PYTHONPATH`.
5. Re-run `python <openmmlab-train-entrypoint> --help` or `python <openmmlab-test-entrypoint> --help` after fixing the import path.

## Backbone checkpoint path or shape mismatch

Symptoms:

- `FileNotFoundError` for the path in `model.backbone.pretrained`
- missing or unexpected keys during checkpoint load
- shape mismatch after editing `dim`, `depths`, `num_heads`, or `window_size`

Actions:

- Keep the config family matched to the published checkpoint family.
- Use the tiny backbone checkpoint with the tiny config, the small checkpoint with the small config, and the base checkpoint with the base config.
- Do not substitute the classification backbone for the detector checkpoint that `<openmmlab-test-entrypoint>` expects.
- If you changed the stem or stage widths, also update `neck.in_channels` to `[dim, 2*dim, 4*dim, 8*dim]`.

## COCO directory or annotation errors

Symptoms:

- `FileNotFoundError` for `instances_train2017.json` or `instances_val2017.json`
- `Found 0 images` during dataloader startup
- train/test runs start but the dataset length is zero or wrong

Actions:

1. Confirm the root looks like:

   ```text
   data/coco/
   ├── annotations/
   │   ├── instances_train2017.json
   │   └── instances_val2017.json
   ├── train2017/
   └── val2017/
   ```

2. Override `data_root` with `--cfg-options data_root=/actual/path/to/coco` when the dataset lives elsewhere.
3. Check that `train2017` and `val2017` contain images and that the annotation JSONs match the image split you are using.
4. Do not point these configs at ADE20K or ImageNet folders; those belong to sibling sub-skills.

## `--eval bbox segm` or metric confusion

Symptoms:

- only box metrics are printed when you expected both box and mask AP
- `segm` is missing or zero because the wrong evaluation flags were used
- a run uses `bbox` metrics but the user compares it to a `bbox+segm` paper number

Actions:

- Use `--eval bbox segm` for the published detection comparison.
- Use `--eval bbox` only when you intentionally want box AP.
- Use `--eval segm` only when you intentionally want mask AP.
- Remember that the README table reports both box and mask AP, so a single-metric run is not directly comparable.

## Slurm or container placeholders

Symptoms:

- shell launchers fail because `partition`, `account`, or `container-image` placeholders were left unchanged
- the command runs on the wrong host because `PYTHONPATH` does not include `tools`
- a shell wrapper hides the actual `python <openmmlab-train-entrypoint>` or `python <openmmlab-test-entrypoint>` command you need to adapt

Actions:

- Treat the published shell wrappers as patterns, not copy-paste launch files.
- Replace the site-specific placeholders with your cluster settings.
- Prefer the direct single-GPU or Slurm command forms in `references/workflows.md` when you need a reproducible command string.
- If a custom launcher does not import `mamba_vision`, add that import before building the model.

## Safe debug order

When several things are wrong at once, debug in this order:

1. Python import surface and pinned package versions.
2. `MM_mamba_vision` registry import.
3. Backbone checkpoint family and path.
4. COCO data root and annotation files.
5. `bbox` vs `segm` metric selection.
6. Slurm or container wrapper details.
