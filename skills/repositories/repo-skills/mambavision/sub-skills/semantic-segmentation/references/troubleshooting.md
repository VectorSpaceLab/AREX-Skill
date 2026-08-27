# Troubleshooting

Use this reference when semantic-segmentation commands fail because of imports, package versions, data layout, checkpoint shape mismatches, or AMP settings.

## OpenMMLab version mismatch or `mmcv` build failure

Symptoms:
- `ImportError`, `undefined symbol`, or registry errors when importing `mmengine`, `mmcv`, `mmsegmentation`, or `mmdet`
- `mmcv` was built against a different PyTorch/CUDA wheel than the one currently installed
- `python <openmmlab-train-entrypoint> --help` fails before showing argparse help

Actions:
1. Reinstall the pinned stack from `configuration.md`.
2. Make sure the active PyTorch wheel is CUDA-enabled.
3. Rebuild or reinstall `mmcv` for the active torch/CUDA combination if the wheel changed.
4. Re-run a small import smoke:

```bash
python - <<'PY'
import torch
import mmengine
import mmcv
import mmseg
import mmdet
import mmpretrain
import mamba_vision
print('torch', torch.__version__)
print('mmcv', mmcv.__version__)
print('mmseg', mmseg.__version__)
print('mmdet', mmdet.__version__)
PY
```

If the import smoke fails, fix the environment before debugging the config.

## `MM_mamba_vision` registry or import errors

Symptoms:
- `KeyError: MM_mamba_vision is not in the MODELS registry`
- `ModuleNotFoundError: No module named 'mamba_vision'`
- the config loads, but the backbone type cannot be built

Actions:
1. Confirm that the selected entry point can import the MambaVision adapter before building the model.
2. If you launch from somewhere else, add the target adapter directory to `PYTHONPATH` first.
3. Confirm that the CLI can import `mamba_vision` before building the runner.
4. Do not replace the adapter with a generic MMSeg backbone name; the configs expect `MM_mamba_vision`.

## ADE20K directory mismatch

Symptoms:
- `FileNotFoundError`
- `Found 0 images`
- missing validation masks or annotation paths
- metrics are nonsense because the train/val split is wrong

Actions:
1. Check the tree:

```text
ADEChallengeData2016/
  images/
    training/
    validation/
  annotations/
    training/
    validation/
```

2. Make sure `data_root` points at `ADEChallengeData2016`, not its parent directory.
3. Keep the published relative subpaths:
   - `images/training`
   - `images/validation`
   - `annotations/training`
   - `annotations/validation`
4. Override `train_dataloader.dataset.data_root`, `val_dataloader.dataset.data_root`, and `test_dataloader.dataset.data_root` together when using a custom path.

## Checkpoint or backbone channel mismatch

Symptoms:
- size mismatch in the backbone or decoder
- unexpected or missing keys during load
- the wrong checkpoint family was attached to the config
- evaluation starts but the model output is obviously wrong

Actions:
1. Keep checkpoint family and config family aligned:
   - tiny checkpoint with tiny config
   - small checkpoint with small config
   - base checkpoint with base config
   - L3 checkpoint with L3 config
2. Do not change `dim` or `in_dim` unless you also change `decode_head.in_channels` and `auxiliary_head.in_channels`.
3. Keep `out_indices=(0, 1, 2, 3)` unless you intentionally redesign the decoder.
4. If you see a channel mismatch, compare the decoder inputs against the stage channel table in `backbone-adapter.md`.

## Crop size, window size, or resolution mismatch

Symptoms:
- unexpected OOM
- attention/window errors
- lower-than-expected validation scores after changing the input size

Actions:
1. Keep the 512x512 configs on 512 crop sizes.
2. Keep the L3 config on 640x640 and its matching dataset recipe.
3. Do not change the `window_size` tuple casually; it is stage-specific.
4. If you need a different crop or test resolution, lower batch size and retest memory headroom.

## L3 AMP instability

Symptoms:
- NaNs
- divergence
- crashes only when mixed precision is enabled
- results differ badly after forcing `--amp`

Actions:
1. Keep the L3 config as shipped; it already switches from `AmpOptimWrapper` to `OptimWrapper`.
2. Do not force `--amp` on the L3 recipe.
3. If you edited the config, restore `OptimWrapper`, then retry.

## Slurm or container placeholder failures

Symptoms:
- copied `*.sh` scripts fail on missing account, partition, image, or mount settings
- cluster wrappers are trying to mount paths that do not exist locally
- `mamba_vision` imports fail only inside a wrapped launcher

Actions:
1. Treat the bundled shell scripts as reference-only command patterns.
2. Prefer the direct single-GPU command patterns in `workflows.md` when debugging.
3. If you need Slurm, keep only the generic `srun` or `sbatch` shell and replace site-specific fields yourself.
4. Ensure the adapter directory remains on `PYTHONPATH` when the launcher changes the working directory.

## Sanity checks

- A healthy single-GPU validation run ends with `aAcc`, `mIoU`, and `mAcc`.
- The published mIoU targets are 46.0, 48.2, 49.1, and 53.2 for tiny, small, base, and L3.
- If the reported metric is far outside that band, recheck the config family, checkpoint, crop size, and ADE20K path first.
