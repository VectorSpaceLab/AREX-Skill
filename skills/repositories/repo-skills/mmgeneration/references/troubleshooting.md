# Troubleshooting

## Purpose

Read this when MMGeneration fails to install, import, sample, train, or evaluate. This page collects cross-cutting failures that affect more than one sub-skill.

## Install and import failures

### `ModuleNotFoundError: No module named 'mmcv.runner'`

**Likely cause:** You installed `mmcv` 2.x or `mmcv-lite` instead of the compatible 1.x `mmcv-full` line.

**Recovery:**
1. Remove the incompatible MMCV package from the environment.
2. Install a 1.x `mmcv-full` wheel that matches your torch/CUDA combination.
3. Reinstall `mmgen` editable or as a wheel.
4. Re-run `python scripts/check_install.py`.

### `setup.py` fails while building the repo

**Likely cause:** `setup.py` imports `torch` at build time, so PyTorch is missing or broken before the repo install begins.

**Recovery:** Install PyTorch first, then install `mmcv-full`, then reinstall the repo.

### `mmcv.ops` import fails

**Likely cause:** The environment has `mmcv` without compiled ops, or the wheel does not match the installed torch/CUDA combination.

**Recovery:**
- For CPU-only inspection, accept that compiled ops are unavailable and keep to the CPU-verifiable workflows.
- For GPU workflows, install a matching `mmcv-full` wheel and re-run the install check with `--check-mmcv-ops`.

## Backend and wheel failures

### `torch.cuda.is_available()` is false on a GPU host

**Likely cause:** Wrong torch wheel, CUDA runtime mismatch, driver issue, or container GPU passthrough is missing.

**Recovery:**
1. Print torch and CUDA versions.
2. Check the driver and visible GPU model.
3. Reinstall a compatible wheel set.
4. Re-run the tiny CUDA tensor smoke in `scripts/check_install.py`.

### CUDA workflows are requested but the host is CPU-only

**Likely cause:** The user needs a GPU workflow, but no GPU is visible.

**Recovery:** Narrow the task to CPU-verifiable inspection, or run the workflow on compatible hardware. Do not pretend the CPU path verified a CUDA-only claim.

## Data and config failures

### Paired or unpaired translation data loads the wrong images

**Likely cause:** The folder structure does not match the dataset class.

**Recovery:**
- Paired data should look like `train/` and `test/` with concatenated images.
- Unpaired data should look like `trainA/trainB/testA/testB`.
- Use `references/data-formats.md` to check the expected keys.

### Custom config inheritance does not behave as expected

**Likely cause:** `_delete_=True` was omitted, `custom_imports` points at the wrong module, or a nested override did not match the original config structure.

**Recovery:** Print the merged config with `sub-skills/configuration-and-extension/scripts/print_config.py` and inspect the final tree.

### Loss or hook registration fails

**Likely cause:** The custom class is not imported into the right package namespace, or the config uses a class name that was never registered.

**Recovery:** Import the module in the relevant `__init__.py` or use `custom_imports`, then re-run the config printer and a small model-build check.

## CLI and API misuse

### `sample_conditional_model` raises a label-length error

**Likely cause:** The label list length does not equal `num_samples`, and the label is not a single value that can be repeated.

**Recovery:** Pass one label, or pass a list whose length exactly matches the requested sample count.

### `sample_img2img_model` asserts on the model type

**Likely cause:** The model is not a `BaseTranslationModel` subclass.

**Recovery:** Use a Pix2Pix or CycleGAN-style translation config, not an unconditional GAN config.

### `translation_eval.py --eval none` crashes

**Likely cause:** The script currently references `args.num_samples` in the no-metric path even though the CLI does not define that argument.

**Recovery:** Avoid the `--eval none` path for this helper unless the script is patched; use the main evaluation script or direct sampling instead.

## Optional-dependency failures

### `apps/styleclip.py` dies immediately with a `clip` import error

**Likely cause:** The optional OpenAI CLIP package is missing.

**Recovery:** Install the optional dependency before running StyleCLIP. Also note that the script currently raises a plain string in the import guard, so the failure is a `TypeError` after the missing-import branch.

### TorchServe packaging fails

**Likely cause:** `torch-model-archiver`, TorchServe, or the handler/runtime assumptions are missing.

**Recovery:** Install the external TorchServe tooling and use the deployment sub-skill to confirm the `.mar` packaging command before starting a server.

## Workflow-specific failures

### `inception_stat.py` needs GPU or download assets

**Likely cause:** The script uses a CUDA Inception path for the StyleGAN-style branch and can fetch remote assets.

**Recovery:**
- For a CPU-only inspection, stick to the PyTorch Inception path and do not claim StyleGAN/Tero backend verification.
- If the script is meant to mirror a StyleGAN metric, ensure the cached script module exists and the GPU runtime is available.

### Distributed evaluation supports only part of the metric set

**Likely cause:** The multi-GPU path is intentionally limited.

**Recovery:** Use the single-GPU or online/offline fallback for unsupported metrics, or restrict the distributed claim to FID/IS as documented.

### CPU training is supported but slow

**Likely cause:** The docs allow CPU training for debugging, not for realistic throughput.

**Recovery:** Use CPU only for configuration and flow validation; use a GPU when you need to claim practical training support.

## When to stop and escalate

Stop and ask for one of the following when the fix requires it:

- A different torch/CUDA wheel family.
- A missing GPU or driver update.
- Network access for model/statistic downloads.
- Optional third-party packages such as CLIP or TorchServe.
- A config or dataset rewrite that changes the workflow being tested.
