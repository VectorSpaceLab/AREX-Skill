# ALAE cross-cutting troubleshooting

## Import path errors

**Symptoms**

- `ModuleNotFoundError: No module named 'net'`
- `ModuleNotFoundError: No module named 'defaults'`
- Subdirectory scripts such as `style_mixing/stylemix.py` or `dataset_preparation/prepare_mnist_tfrecords.py` fail immediately.

**Cause**

ALAE is not packaged; subdirectory scripts import root modules directly.

**Recovery**

```bash
cd <ALAE-checkout>
export PYTHONPATH="$PYTHONPATH:$(pwd)"
python style_mixing/stylemix.py -c ffhq
```

Or run from an IDE with the working directory set to the checkout root.

## PyTorch/CUDA backend errors

**Symptoms**

- `torch.cuda.is_available()` is false.
- `no kernel image is available for execution on the device`.
- ALAE scripts fail at `torch.cuda.set_device(0)` or `.cuda()`.

**Cause**

Core training/generation scripts are CUDA-first. README-era PyTorch 1.4/CUDA10 may not support newer GPUs such as A100.

**Recovery**

- Install a CUDA-enabled PyTorch wheel compatible with the actual GPU and driver.
- On A100-class machines, use a CUDA11-capable PyTorch stack or newer rather than the old CUDA10 wheel.
- Run the root checker from this skill: `python scripts/check_alae_environment.py --repo-root <ALAE-checkout>`.
- Do not treat CPU-only PyTorch import as proof that training/generation routes are ready.

## Requirements issues

**Symptoms**

- Installing `requirements.txt` fails on `sklearn`.
- `make_recon_figure_multires.py` fails with `ModuleNotFoundError: No module named 'skimage'`.
- `dlutils` fails to import against a very new PyTorch.

**Recovery**

- Install `scikit-learn` instead of the deprecated `sklearn` shim.
- Install `scikit-image` for the multi-resolution reconstruction figure route.
- If `dlutils` imports fail because a PyTorch internal moved, choose an older CUDA-capable PyTorch compatible with your GPU rather than blindly upgrading.

## TensorFlow/dnnlib legacy metric errors

**Symptoms**

- `AttributeError: module 'tensorflow' has no attribute 'Session'`.
- `AttributeError: module 'tensorflow' has no attribute 'python_io'`.
- TensorFlow warns about missing `libcudart.so.10.0` or `libcudnn.so.7`.
- Metric scripts start unexpected downloads during import.

**Cause**

Dataset-preparation and metric scripts use TensorFlow 1.x/StyleGAN-era APIs. Metrics also rely on `dnnlib` and pickle assets.

**Recovery**

- Use a Python/TensorFlow 1.x-compatible environment for TFRecord scripts and metrics.
- Install the StyleGAN `dnnlib` wheel referenced by the README when running metrics.
- Do not import `metrics/*.py` just to inspect them; run `sub-skills/metrics/scripts/check_metrics_stack.py` instead.
- Full metric execution needs explicit user approval, data, checkpoints, metric pkl files, and a compatible legacy TensorFlow GPU stack.

## Missing checkpoints and `last_checkpoint`

**Symptoms**

- `FileNotFoundError` or checkpoint load warnings.
- Generation/metrics checkers report `last_checkpoint points to a file that was not found`.

**Cause**

Model-loading scripts read `OUTPUT_DIR/last_checkpoint`, then load the path written inside it. The pointer may refer to a model file that has not been downloaded, trained, or copied to the current machine.

**Recovery**

- Use `scripts/download_alae_artifacts.py --dataset <name>` to list expected pretrained files.
- Download or train the checkpoint, then update `OUTPUT_DIR/last_checkpoint` to the actual `.pth` path.
- If model architecture fields changed since checkpoint creation, expect missing/unexpected key warnings; check `sub-skills/training/references/checkpoints.md`.

## Data path and TFRecord errors

**Symptoms**

- `FileNotFoundError` under `/data/datasets/...`.
- `AssertionError` from `TFRecordsDataset` about part counts.
- Training hangs or fails when a TFRecord resolution/part is missing.

**Recovery**

- Run `sub-skills/data-preparation/scripts/validate_alae_data_layout.py --repo-root <ALAE-checkout> --config-file <config>` before training.
- Override `DATASET.PATH`, `DATASET.PATH_TEST`, `PART_COUNT`, and `PART_COUNT_TEST` with YACS trailing options when using custom data.
- Ensure `PART_COUNT % world_size == 0` for distributed training.
- Do not run raw dataset conversion scripts until disk, raw data, and TensorFlow 1.x requirements are confirmed.

## Stale README and absent files

The README names ablation/separate-model routes (`train_alae_separate.py`, `model_separate.py`, and `celeba_ablation_*.yaml`) that are absent in this checkout. Do not route users to those files unless a newer checkout actually contains them. `metrics/fid_sep.py` is also excluded because it imports the absent `model_separate.py`.

## Network side effects

`training_artifacts/download_all.py`, `metrics/*.py`, and some dataset scripts call download helpers at module import or run time. Prefer generated dry-run/check scripts first, get explicit approval for network downloads, and record where large artifacts will be written.
