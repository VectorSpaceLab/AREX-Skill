# Troubleshooting

Use this page for cross-cutting problems that can block multiple workflows.

## Missing or mismatched Python packages

### Symptoms
- `ModuleNotFoundError` for `torch`, `torchvision`, `visdom`, `dominate`, `GPUtil`, or `cv2`.
- `python -m pip check` reports broken requirements.
- Importing `train`, `test`, `models.*`, or dataset helpers fails immediately.

### Likely causes
- The environment does not have a compatible PyTorch/torchvision pair.
- Optional workflow dependencies were skipped.
- The checkout is being run from the wrong Python environment.

### Recovery
- Reinstall a compatible `torch`/`torchvision` pair for the host backend.
- Install `visdom`, `dominate`, and `GPUtil` for the translation and launcher workflows.
- Install `opencv-python-headless` when using the dataset-preparation helpers that import `cv2`.
- Re-run the shared smoke helper in `scripts/check_runtime.py`.

## Legacy warnings from `cycle_gan_model.py`

### Symptoms
- Importing `models.cycle_gan_model` prints `No module named 'apex'`.
- A CycleGAN run hits an attribute error around `opt.amp`.

### Likely causes
- The legacy CycleGAN path still imports optional AMP tooling, but the current checkout does not define a matching CLI flag.

### Recovery
- Treat CycleGAN as a legacy/stale path in this checkout.
- Prefer CUT/FastCUT/SinCUT workflows unless you intentionally patch the legacy model.
- Do not confuse the warning with a failure in CUT or SinCUT.

## Stale README examples

### Symptoms
- A user tries `python test.py --model test ...` from the README and gets a model resolution error.

### Likely causes
- This checkout does not contain `models/test_model.py`.

### Recovery
- Use the supported model routes instead: CUT/FastCUT through `--model cut` plus `--CUT_mode`, or SinCUT through `--model sincut`.
- For one-image-per-domain workflows, use the single-image dataset and SinCUT path instead of the stale example.

## CUDA / GPU / memory issues

### Symptoms
- `torch.cuda.is_available()` is false on a GPU host.
- Training or testing fails with CUDA memory errors.
- Multi-GPU commands select the wrong devices.

### Likely causes
- CPU-only torch build, incompatible wheel, missing driver/runtime, or too-large batch/crop settings.

### Recovery
- Verify the active environment with `scripts/check_runtime.py`.
- Reduce batch size, crop size, or image resolution.
- Set `--gpu_ids -1` for CPU smoke checks or a concrete GPU list for training.
- Use the translation-workflows reference for the verified option names.

## Checkpoint and output-path confusion

### Symptoms
- The model loads the wrong checkpoint or writes outputs to an unexpected directory.
- HTML results do not appear where the user expects.

### Likely causes
- `--checkpoints_dir`, `--results_dir`, `--name`, `--phase`, or `--epoch` were not set as intended.

### Recovery
- Re-read the workflow reference for the exact output conventions.
- Confirm whether the user wants training outputs in `checkpoints/<name>/web/` or test outputs in `results/<name>/<phase>_<epoch>/`.

## `python -m experiments` problems

### Symptoms
- `python -m experiments ... dry` fails.
- The CLI reports that `id` is required.
- tmux windows are created or closed unexpectedly.

### Likely causes
- The launcher CLI expects `name cmd id ...`, and the current `dry` path is broken because it calls `launch(dry=True)` without ids.

### Recovery
- Use the safe command-list helper in `sub-skills/experiment-launchers/scripts/list_experiment_commands.py`.
- Use `print_names` / `print_test_names` for inspection only.
- Do not rely on `dry` in this checkout.

## When to stop and ask for more data

Stop and ask when the user needs external trained checkpoints, a downloaded dataset, or hardware that is not present. Those prerequisites are outside the skill itself.
