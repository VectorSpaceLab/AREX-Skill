# Troubleshooting

## Purpose

Use this file for install, backend, config, or runtime failures that affect more than one workflow.

## Common failures

### `pytorch-lightning==1.5.6` will not install on a modern pip

**Symptom:** pip rejects the wheel metadata with a message about `torch>=1.7.*` or says the version is unavailable.

**Likely cause:** pip 24.1+ enforces stricter metadata parsing that this older Lightning release does not satisfy.

**Fix:** pin pip below 24.1 in the inspection environment before installing the repo requirements.

### `pkg_resources` or `six` is missing during Lightning import

**Symptom:** `ModuleNotFoundError: No module named 'pkg_resources'` or `No module named 'six'` when importing `pytorch_lightning` or `torch.utils.tensorboard`.

**Likely cause:** the environment is missing the compatibility packages used by the old Lightning/TensorBoard stack.

**Fix:** ensure `setuptools` is installed with `pkg_resources` and add `six`.

### `numpy` 2.x triggers warnings or import failures in old compiled modules

**Symptom:** import warnings about modules compiled with NumPy 1.x or failures inside torchvision / torch extensions.

**Likely cause:** the environment pulled NumPy 2.x into a stack built against NumPy 1.x.

**Fix:** use `numpy<2` for this repo's legacy stack.

### `run.py` fails before training starts

**Symptom:** `KeyError` on `data_params`, `TypeError` from `len(config['trainer_params']['gpus'])`, or `KeyError` for an unknown model name.

**Likely cause:** the config schema does not match the generic runner, or the model name is not registered in `models.vae_models`.

**Fix:** use the bundled training wrapper and the config layout documented in the training sub-skill. Check whether the config is a legacy VampVAE-style file before guessing.

### CUDA sample or train paths fail on CPU-only hardware

**Symptom:** `.cuda()` errors, device mismatch errors, or `torch.cuda.is_available()` is false.

**Likely cause:** the selected workflow is GPU-oriented and some model sample methods or training configs assume CUDA.

**Fix:** run on a CUDA-capable host or restrict the task to CPU-safe model smoke checks only.

### DFCVAE appears to download pretrained weights

**Symptom:** model instantiation stalls or tries to fetch VGG19-BN weights.

**Likely cause:** `DFCVAE` builds a frozen VGG19-BN feature network with `pretrained=True`.

**Fix:** allow the download, pre-cache the weights, or avoid this model in offline-only environments.

## Where to go next

- Training/config errors: `sub-skills/training/references/troubleshooting.md`
- Model API and sample/generate issues: `sub-skills/model-reference/references/troubleshooting.md`
- Exact signatures and model-specific kwargs: `sub-skills/model-reference/references/api-reference.md`
