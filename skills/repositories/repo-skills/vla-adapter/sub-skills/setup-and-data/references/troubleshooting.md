# Troubleshooting

This note collects the common setup and data issues that show up before training or deployment.

## Quick symptom table

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `flash-attn` fails to build or import | Torch / CUDA / FlashAttention mismatch, or install order is wrong | From `cd "$VLA_ADAPTER_REPO_ROOT"`, install torch first, then `python -m pip install -e "$VLA_ADAPTER_REPO_ROOT"`, then `flash-attn==2.5.5 --no-build-isolation`. If the wheel still fails, clear the pip cache for `flash_attn` and pick the wheel that matches your CUDA version. Verify `ninja --version` succeeds. |
| `AttributeError: 'NoneType' object has no attribute 'eglQueryString'` | Missing EGL / Mesa runtime packages | Install the Mesa stack the README lists: `libgl1-mesa-dev`, `libegl1-mesa-dev`, `libgles2-mesa-dev`, and `libglew-dev`. This appears in both LIBERO and CALVIN paths. |
| LIBERO dataset download exists but the loader still misses it | The archive kept the `modified_` prefix | Rename or alias the local folder so the builder names are `libero_spatial_no_noops`, `libero_object_no_noops`, `libero_goal_no_noops`, and `libero_10_no_noops`. The benchmark code expects the unmodified names. |
| CALVIN scripts cannot find the native repo or config files | `CALVIN_ROOT` layout mismatch | The CALVIN eval code seeds `CALVIN_ROOT` with the literal `calvin` path. Create a `calvin/` symlink or edit the script if your checkout lives elsewhere. If `pyhash` installation fails, the README recommends `setuptools==57.5.0`. |
| Inference warns about missing `dataset_statistics.json` or `unnorm_key` | The checkpoint directory is incomplete | Make sure the run directory contains `config.json`, `dataset_statistics.json`, and a `checkpoints/` folder with `.pt` files. Local loaders read `dataset_statistics.json` to denormalize actions. |
| ALOHA offline loading breaks after setup | `setup_training.sh --local-models` rewrote source files to local paths | Confirm `ROOT_DIR`, `LOCAL_QWEN_PATH`, and `LOCAL_TIMM_PATH` are set before enabling local models. To return to hub-backed loading, restore `prismatic/models/backbones/llm/qwen25.py`, `prismatic/models/materialize.py`, and `prismatic/models/backbones/vision/dinosiglip_vit.py`. |

## Notes by area

### Torch / FlashAttention

The published install order matters:

1. install PyTorch 2.2.0 family first
2. install the package in editable mode
3. install `flash-attn==2.5.5` without build isolation

If you are using a wheel, choose the one that matches the CUDA build reported by `nvidia-smi`. One known-good example mentioned in the README is `flash_attn-2.5.5+cu122torch2.2cxx11abiFALSE-cp310-cp310-linux_x86_64.whl`.

### LIBERO path hygiene

The HF download name uses `modified_libero_rlds`, but the training config and dataset registry expect the unprefixed dataset names. If the validation script can see `modified_` in the path, it should be treated as a warning.

### CALVIN loader behavior

Some CALVIN code paths assume a relative `calvin/` checkout and look under `calvin_models/conf`. The setup router should treat that as an environment expectation, not as a data-root convention. If you only have the RLDS archive, the benchmark data is still separate from the native CALVIN repo.

### Checkpoint completeness

When a checkpoint directory is missing `dataset_statistics.json`, the model may still load, but action de-normalization and `predict_action()` can fail later. Validate the directory before handing it to evaluation or deployment.

### ALOHA source mutation caution

The local-model workflow is intentionally invasive because it replaces source files with offline-loading variants. Do not enable `--local-models` until you are sure the local mirror paths are correct, and restore the touched files before switching back to hub-backed execution.

