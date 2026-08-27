# Cross-Cutting Troubleshooting

Use this reference for failures that can affect multiple MMSegmentation workflows. For task-specific issues, also read the nearest sub-skill troubleshooting file.

## `ModuleNotFoundError: mmseg` or Wrong Package

Likely causes:

- `mmsegmentation` is not installed in the active Python environment.
- The command is using a different Python than the one used for installation.
- Editable source install was not run after cloning.

Checks:

```bash
python -c "import sys; print(sys.executable)"
python -m pip show mmsegmentation
python -c "import mmseg; print(mmseg.__version__)"
```

Fix by installing `mmsegmentation` into the same Python used to run the command.

## `mmcv` or `mmengine` Version Assertion

MMSegmentation imports assert compatible OpenMMLab foundations. For this snapshot, use `mmcv>=2.0.0rc4,<2.2.0` and `mmengine>=0.5.0,<1.0.0`.

If import fails with a version assertion:

1. Print installed versions.
2. Install a matching `mmcv` wheel for the active PyTorch/CUDA or CPU runtime.
3. Avoid mixing `mmcv-lite` when compiled ops are required.
4. Re-run `python -m pip check`.

## `No module named mmcv._ext` or `mmcv.ops`

Likely causes:

- `mmcv-lite` is installed instead of full `mmcv`.
- The full `mmcv` wheel does not match the installed `torch` version or backend.
- A model/head/project requires compiled MMCV ops unavailable in the current environment.

Fix by installing full `mmcv` for the current `torch` and backend, or choose a model/config that does not require compiled ops in a minimal CPU environment.

## Torch, NumPy, and OpenCV ABI Warnings

Symptoms include `_ARRAY_API not found`, warnings about modules compiled using NumPy 1.x, or `pip check` conflicts involving `opencv-python` and NumPy.

Fix path:

```bash
python -m pip install "numpy<2" "opencv-python<4.12"
python -m pip check
python -c "import torch, mmcv, mmseg; print(torch.__version__, mmcv.__version__, mmseg.__version__)"
```

If a newer PyTorch/MMCV stack supports NumPy 2 in the user's environment, upgrading the whole stack can also be valid. Do not mix partial upgrades blindly.

## CUDA Unavailable

Symptoms:

- `torch.cuda.is_available()` is `False` on a GPU host.
- Inference/training defaults to `cuda:0` and fails.
- Error messages mention missing CUDA libraries or incompatible drivers.

Checks:

```bash
nvidia-smi
python - <<'PY'
import torch
print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.device_count())
PY
```

Fix by installing a CUDA-enabled PyTorch wheel compatible with the driver and matching MMCV. For deterministic smoke checks, pass `device='cpu'` or set `CUDA_VISIBLE_DEVICES=-1`.

## Config Errors

Common config symptoms:

- Missing `_base_` path.
- Wrong `--cfg-options` syntax.
- Unknown registry `type`.
- `tta_pipeline` or `tta_model` missing when using TTA.

Use the data-configuration helper:

```bash
python sub-skills/data-configuration/scripts/inspect_mmseg_config.py --config PATH/TO/MMSEG_CONFIG.py --show-keys model train_dataloader test_evaluator
```

If a custom type is missing, use the model-customization registry helper and check `custom_imports`.

## Dataset and Annotation Failures

Common causes:

- Image and mask suffixes do not match config defaults.
- `data_root` or `data_prefix` points to the wrong directory.
- `reduce_zero_label` or `ignore_index` does not match dataset labels.
- Annotation loading remains in a hidden-test pipeline with no labels.

Use:

```bash
python sub-skills/data-configuration/scripts/check_dataset_layout.py --img-dir PATH/TO/IMAGES --ann-dir PATH/TO/MASKS --img-suffix .jpg --seg-map-suffix .png
```

Then inspect the selected config fields with the config helper.

## Checkpoint and Class-Metadata Failures

Symptoms:

- Missing/unexpected keys.
- Shape mismatch in decode head or classifier layers.
- Visualized colors/classes look wrong.
- A checkpoint lacks `dataset_meta`.

Checks:

- Verify the checkpoint was trained for the selected config family and class count.
- Check `model.dataset_meta`, `num_classes`, `out_channels`, and class/palette overrides.
- For fine-tuning, expect dataset-specific decode-head weights to differ when class counts change.

## Long-Running or Side-Effectful Commands

Training, testing on real datasets, dataset conversion, checkpoint conversion, benchmarking, distributed jobs, and downloads can be expensive or mutating. Use bundled dry-run/helper modes first, then ask the user before executing.
