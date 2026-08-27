# Troubleshooting

## Registry miss

**Symptoms**
- `KeyError` from `get_module`
- A config file names a model, dataset, or pipeline that cannot be found

**Likely causes**
- The class name is misspelled.
- The framework string is wrong for a framework-specific registry lookup.
- The requested class exists only in the other backend.

**Recovery**
- Check the exact registered class names.
- Confirm whether you are using `torch` or `tf`.
- Use the bundled command builder to inspect the config before launching.

## Config merge confusion

**Symptoms**
- CLI overrides do not appear to take effect.
- The wrong dataset path or split is used.

**Likely causes**
- The override key does not match the config structure.
- The dataset/model/pipeline sections were merged in a different order than
  expected.

**Recovery**
- Inspect the merged command shape with
  `scripts/build_run_pipeline_command.py`.
- Double-check `dataset_path`, `split`, `device`, and `ckpt_path` fields.

## Open3D / torch version mismatch

**Symptoms**
- `open3d.ml.torch` reports a version mismatch.
- Import succeeds for `open3d` but fails once `open3d.ml.torch` is imported.

**Likely causes**
- The installed torch wheel is outside the Open3D wheel's expected version
  band.

**Recovery**
- Reinstall a compatible torch/torchvision pair.
- Re-run the install-and-inspect smoke helper before doing anything else.

## Missing PyTorch ops

**Symptoms**
- `open3d` imports, but `open3d.ml.torch` is unavailable or incomplete.

**Likely causes**
- The Open3D wheel does not expose PyTorch ops for the current platform.

**Recovery**
- Use an Open3D build that includes the required backend.
- Treat the path as blocked until the backend is available.

## Invalid dataset split or path

**Symptoms**
- Training or inference code raises when constructing the dataset.
- A split object exists but returns no data.

**Likely causes**
- The dataset path is wrong.
- The split name does not match the dataset's accepted split names.

**Recovery**
- Route back to the dataset sub-skill and validate the folder layout first.

## Checkpoint / download assumptions

**Symptoms**
- A workflow assumes pretrained weights, but the checkpoint is missing.

**Likely causes**
- The command references a checkpoint that was never downloaded or copied.

**Recovery**
- Make the checkpoint path explicit.
- Do not hide the download step behind a silent helper when network access is
  unavailable.

## Long-running training safety

**Symptoms**
- A task tries to launch a full training run in a smoke-check environment.

**Likely causes**
- The user asked for a large training job when only API inspection was needed.

**Recovery**
- Use the helper to inspect the command shape, not to launch the full job.
- Keep expensive training outside the default verification path.
