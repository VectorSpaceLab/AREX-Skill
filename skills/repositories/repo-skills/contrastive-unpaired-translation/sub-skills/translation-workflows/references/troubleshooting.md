# Troubleshooting

Use this page for workflow-specific problems that affect CUT, FastCUT, or SinCUT usage.

## Import or install failures

### Symptoms
- `ImportError` or `ModuleNotFoundError` for `torch`, `torchvision`, `visdom`, `dominate`, `GPUtil`, or related modules.
- `python scripts/check_runtime.py --repo-root .` reports missing required imports.
- `python train.py --help` or `python test.py --help` fails before printing options.

### Likely causes
- The active environment does not contain a compatible PyTorch/torchvision pair.
- Optional runtime dependencies were not installed.
- The repo is being inspected from the wrong Python environment.

### Recovery
- Reinstall a matching `torch`/`torchvision` pair for the host backend.
- Install `visdom`, `dominate`, and `GPUtil` if you need the visualizer or launcher paths.
- Re-run `scripts/check_runtime.py --repo-root . --check-cuda`.

## CUDA or GPU problems

### Symptoms
- `torch.cuda.is_available()` is false on a GPU host.
- Training fails with CUDA OOM or device mismatch errors.
- Multi-GPU settings select the wrong device list.

### Likely causes
- CPU-only torch build, incompatible wheel, missing driver/runtime, or overly large batch/crop settings.

### Recovery
- Confirm the runtime with the bundled checker.
- Reduce `--batch_size`, `--crop_size`, or `--load_size`.
- Use `--gpu_ids -1` for CPU smoke tests or a concrete GPU list for training.

## Checkpoint or result-path confusion

### Symptoms
- The model loads the wrong run or writes results in an unexpected place.
- HTML results are missing.

### Likely causes
- `--name`, `--checkpoints_dir`, `--results_dir`, `--epoch`, or `--phase` were not set as intended.

### Recovery
- Training checkpoints live under `checkpoints/<name>/`.
- HTML training snapshots live under `checkpoints/<name>/web/` when HTML is enabled.
- Test results live under `results/<name>/<phase>_<epoch>/`.
- Recheck the exact flag family in `references/cli-reference.md`.

## Pretrained model loading failures

### Symptoms
- `load_networks` cannot find the expected `*_net_*.pth` file.
- A pretrained run points at the wrong experiment name.

### Likely causes
- The checkpoint epoch or checkpoint root does not match the saved model.

### Recovery
- Verify `--checkpoints_dir`, `--name`, `--epoch`, and `--pretrained_name`.
- Confirm the file naming convention from `BaseModel.save_networks`.

## Legacy CycleGAN warnings

### Symptoms
- Importing `models.cycle_gan_model` prints `No module named apex`.
- A CycleGAN run reaches an `amp`-related error.

### Likely causes
- The legacy CycleGAN module still references optional AMP tooling, but the current checkout does not wire an `--amp` option through the parser.

### Recovery
- Treat this as a legacy path, not a supported CUT/FastCUT/SinCUT route.
- Do not let the warning hide a successful CUT or SinCUT setup.

## Stale README command

### Symptoms
- A user tries the README's `--model test` example and gets a model resolution error.

### Likely causes
- The checkout does not include a `models/test_model.py` implementation.

### Recovery
- Use `--model cut` or `--model sincut` instead.
- For one-image-per-domain use SinCUT plus the single-image dataset layout.

## When to stop

Stop and ask for more data when the task requires external checkpoints, a downloaded dataset, or unavailable hardware. Those are prerequisites, not skill bugs.
