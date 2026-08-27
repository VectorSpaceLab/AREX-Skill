# Training Workflows

## Purpose

Read this when you want to run a PyTorch-VAE experiment from a config and need the end-to-end flow, not just the config keys.
The example commands below assume the generated skill directory is the current working directory.

## Standard flow

1. Choose a config under `configs/` that matches the model family.
2. Make sure the dataset root points at an extracted CelebA tree.
3. Run the bundled wrapper in validation mode first.
4. Re-run with `--fit` only after the config and backend are ready.

Example validation pass:

```bash
python ./sub-skills/training/scripts/train_from_config.py \
  --repo-root /path/to/PyTorch-VAE \
  --config /path/to/PyTorch-VAE/configs/vae.yaml
```

Example full run:

```bash
python ./sub-skills/training/scripts/train_from_config.py \
  --repo-root /path/to/PyTorch-VAE \
  --config /path/to/PyTorch-VAE/configs/vae.yaml \
  --fit
```

## What the wrapper does

- imports the repo modules from the checkout you pass with `--repo-root`
- loads the YAML config with `PyYAML`
- instantiates the model from `models.vae_models`
- builds `VAEDataset`
- validates the data path with `setup()`
- runs the Lightning trainer only when `--fit` is present

## Output locations

- TensorBoard logs: `logs/<logging_params.name>/version_*`
- Checkpoints: the logger's `checkpoints/` subdirectory
- Sample reconstructions: `Reconstructions/` under the same logger directory
- Random samples: `Samples/` under the same logger directory

## Special training cases

- **FactorVAE**: needs the discriminator-related `exp_params` keys such as `submodel`, `LR_2`, and `scheduler_gamma_2`.
- **VampVAE**: uses a legacy config layout; the bundled wrapper normalizes it so the generic training path can still validate it.
- **ConditionalVAE**: the model expects label vectors, not scalar class ids.

## When not to use this flow

If the user only wants the constructor signature, latent-shape details, or sample/generate behavior, switch to the model-reference sub-skill instead.
