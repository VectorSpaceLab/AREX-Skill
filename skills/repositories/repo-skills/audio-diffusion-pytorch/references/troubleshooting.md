# Troubleshooting

This page covers install/import, optional dependency, backend, and cross-cutting workflow issues. For workflow-specific failures, open the nearest sub-skill troubleshooting page:

- `sub-skills/generation/references/troubleshooting.md` for generator, text-conditioning, sampler, and inpainting errors.
- `sub-skills/conditioning/references/troubleshooting.md` for upsampler, vocoder, autoencoder, mel, encoder, adapter, and custom-loss errors.

## Install and import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'audio_diffusion_pytorch'` | The distribution is not installed in the active Python environment | Run `pip install audio-diffusion-pytorch`, then run `scripts/check_install.py --pretty`. |
| `pip show audio-diffusion-pytorch` works but imports fail | A different Python environment is running the task | Use `python -m pip show audio-diffusion-pytorch` and `python -c 'import audio_diffusion_pytorch'` from the same Python executable. |
| `a_unet`, `torch`, `torchaudio`, or `einops` import errors | Base package dependencies are missing or the install is incomplete | Reinstall the package in the target environment and run `python -m pip check`. |
| There is no package CLI | The repository exposes Python APIs rather than console entry points | Use the bundled scripts and Python API recipes instead of looking for a command-line tool. |

## Optional dependencies

| Feature | Extra dependency | Notes |
| --- | --- | --- |
| Text-conditioned generation | `transformers` | The default `a-unet` text path uses a T5 embedder; first use can consult Hugging Face cache or network. |
| README-style autoencoder encoder | `audio_encoders_pytorch` | Optional; `DiffusionAE` only requires an encoder object with `out_channels`, `downsample_factor`, and a compatible `forward`. |
| README/test-style custom spectral loss | `auraloss` | Optional; pass any compatible loss callable as `loss_fn=...`. |

If optional dependency setup is not the user's actual goal, keep the workflow on the dependency-free tiny smoke path first.

## Backend and device

- CPU is sufficient for the bundled smoke scripts and API inspection.
- CUDA can speed real workloads, but the package does not require a CUDA-only code path.
- Keep model parameters, noise tensors, masks, mel tensors, and latent tensors on the same device.
- Use a PyTorch/torchaudio pair from the same package ecosystem. If CUDA import fails, first check `python -m pip check`, then run `scripts/check_install.py --check-cuda --pretty`.
- Do not treat a successful CPU import as proof that a user-provided CUDA wheel, driver, or device placement works.

## No pretrained weights or blessed configs

The package README states that pretrained models are not provided and that shown configs are indicative. When a user asks to "generate audio now":

1. Ask whether they have local weights/checkpoints.
2. If they do not, explain that random weights only validate shapes and execution.
3. Use the tiny scripts for smoke checks, not for quality claims.
4. If the user wants training, require their dataset, objective, optimizer, checkpointing, and evaluation plan; the package itself does not supply a full training pipeline.

## Cross-cutting shape gotchas

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| GroupNorm says channel count is not divisible by groups | `UNetV0` defaults to `resnet_groups=8` but a tiny config uses fewer channels | Set `resnet_groups=1` for smoke tests or choose channel widths divisible by 8. |
| Constructor asserts on list lengths | `channels`, `factors`, `items`, and optional attention/context lists have different lengths | Make all layer-wise lists the same length. |
| A wrapper returns an unexpected length | Input length, resampling factor, mel hop, or latent factor is not aligned | Use tiny even lengths first; then adjust wrapper-specific parameters in the relevant sub-skill. |
| Sampling is slow or memory-heavy | README tensor sizes are large and random weights do not need that scale for smoke tests | Start with the bundled tiny scripts; only scale when real training/inference assets exist. |
