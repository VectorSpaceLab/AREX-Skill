# Troubleshooting

## Scope

This page covers cross-cutting failures that affect multiple EdgeConnect workflows. For workflow-specific details, read the nearest sub-skill reference first.

## PyYAML 6.x breaks config loading

**Symptom**

`Config(...)` fails with:

```text
TypeError: load() missing 1 required positional argument: 'Loader'
```

**Cause**

`src/config.py` uses `yaml.load(...)` in the legacy style. PyYAML 6.x removed the implicit loader default.

**Fix**

- Pin PyYAML to a 5.4.x-compatible build, or
- patch the loader call in the source code if you are maintaining the repository.

## Legacy SciPy image helpers are missing

**Symptom**

Imports fail around `scipy.misc.imread` or `scipy.misc.imresize`.

**Cause**

The repo depends on older SciPy behavior that modern releases removed.

**Fix**

- Use a legacy-compatible SciPy build such as 1.2.x for runtime inspection, or
- patch the code to Pillow/imageio-based loaders if you are modernizing the repository.

## CUDA is visible but the repo still falls back to CPU

**Symptom**

`torch.cuda.is_available()` is false, or the code runs on CPU even though the host has NVIDIA GPUs.

**Cause**

The installed Torch wheel may be CPU-only, the CUDA tag may not match the host driver, or the visible GPU list is wrong.

**Fix**

- Verify the wheel tag with `scripts/check_env.py`.
- Confirm the `GPU` list in the config.
- Reinstall a CUDA-enabled Torch build that matches the host.

## VGG19 pretrained weights fail to load

**Symptom**

Training starts but perceptual/style losses fail during first use, or Torchvision tries to fetch pretrained VGG weights.

**Cause**

The `PerceptualLoss` and `StyleLoss` modules instantiate pretrained VGG19 features.

**Fix**

- Pre-cache the required weights in a networked environment, or
- allow the current run to use a networked first fetch if that is acceptable.

## Checkpoint fallback created the wrong config

**Symptom**

`train.py` or `test.py` created a fresh `config.yml` in the checkpoint directory, but the paths do not match the intended run.

**Cause**

The wrapper copies `config.yml.example` when the checkpoint config is missing.

**Fix**

- Create the intended `config.yml` manually before launching a run.
- Use the bundled checkpoint/config checker in the `testing` sub-skill when you want to validate the directory first.

## The smoke checker fails before imports

**Symptom**

`scripts/check_env.py` cannot import repo modules or instantiate the example config.

**Cause**

The repo root was not supplied, the checkout path is wrong, or the environment still has an incompatible legacy dependency.

**Fix**

- Pass the correct checkout root with `--repo-root`.
- Revisit `references/installation.md` and re-check PyYAML, SciPy, scikit-image, and Torch.

## Where to go next

- Use `data-preparation` for flist, mask, edge, and config-path failures.
- Use `training` for stage, checkpoint, loss, and sampling issues.
- Use `testing` for checkpoint layout and inference command problems.
- Use `evaluation` for pixel metrics, FID preflight, or output-pairing issues.
