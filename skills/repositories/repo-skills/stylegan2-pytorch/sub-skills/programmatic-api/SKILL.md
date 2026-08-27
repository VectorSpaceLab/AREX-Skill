---
name: programmatic-api
description: "Guides Python ModelLoader, Trainer, and StyleGAN2 API usage for
  loading stylegan2_pytorch checkpoints and generating image tensors."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Programmatic API and Checkpoint Sampling

Use this sub-skill when the user wants Python code instead of the
`stylegan2_pytorch` CLI, especially for loading a trained checkpoint with
`ModelLoader`, converting latent noise to styles, generating image tensors, and
saving samples.

## Start here

1. Confirm the environment with the root checker:
   [`../../scripts/check_install.py`](../../scripts/check_install.py). The
   package requires CUDA at import time.
2. Read [references/api-reference.md](references/api-reference.md) for verified
   signatures and how `ModelLoader`, `Trainer`, and checkpoint files relate.
3. Read [references/workflows.md](references/workflows.md) for loading and
   sampling recipes.
4. Use [references/troubleshooting.md](references/troubleshooting.md) if a
   checkpoint is missing, `base_dir` is wrong, tensor shapes/devices are wrong,
   or a package-version mismatch prevents loading.
5. For CLI training or checkpoint creation, route to
   [training](../training/SKILL.md).

## Common task routes

- **Load the latest trained generator:** use `ModelLoader(base_dir=..., name=...)`
  with the directory where the CLI was invoked, assuming the default
  `models/<name>/` layout exists.
- **Load a specific checkpoint:** pass `load_from=<checkpoint_number>` to
  `ModelLoader`.
- **Generate images from random noise:** create a CUDA noise tensor with latent
  dimension `512`, call `noise_to_styles`, then call `styles_to_images`.
- **Save image tensors:** use `torchvision.utils.save_image`; outputs are
  clamped to `[0, 1]` by `styles_to_images`.
- **Custom checkpoint layout:** if training used a non-default `--models_dir`,
  either restore the default `base_dir/models/<name>/` layout for `ModelLoader`
  or use `Trainer` directly with matching `models_dir`.

## Bundled helper script

[`scripts/sample_from_checkpoint.py`](scripts/sample_from_checkpoint.py) adapts
the README `ModelLoader` snippet into a reusable checker that loads a checkpoint
from the default layout and writes a sample grid. Run it only after a checkpoint
exists:

```bash
python sub-skills/programmatic-api/scripts/sample_from_checkpoint.py \
  --base-dir /path/to/run-base \
  --name my-project \
  --output-dir /tmp/sg2-samples
```

## Boundaries

- Do not use this sub-skill to build full training commands, tune augmentation,
  or plan multi-GPU runs; route those to [training](../training/SKILL.md).
- Do not claim CPU-only support. `ModelLoader.noise_to_styles` and
  `styles_to_images` move data to CUDA and the package import already requires
  CUDA.
- Do not tell future agents to open original source files. API facts are
  distilled into this sub-skill's references and helper script.
