# Cross-Cutting Troubleshooting

## Install/import failures

Symptoms include `ModuleNotFoundError: denoising_diffusion_pytorch` or missing dependencies such as `torch`, `torchvision`, `accelerate`, `einops`, `ema_pytorch`, `pytorch_fid`, `scipy`, `PIL`, or `tqdm`.

Fix:

```bash
python -m pip install denoising-diffusion-pytorch
python scripts/check_env.py --device cpu
```

Use the distribution name with hyphens for installation and metadata, and the underscore package name for imports.

## No CLI command exists

This package is Python-API first. If a user asks for a command-line invocation, generate a small Python script using the relevant sub-skill instead of searching for console entry points.

## CUDA requested but unavailable

- Run `python scripts/check_env.py --device auto` to inspect PyTorch and CUDA visibility.
- Use `--device cpu` for smoke scripts on CPU-only machines.
- Do not claim GPU or flash speed from CPU success. Treat CUDA as optional unless the task explicitly requires it.

## Accelerate and training side effects

`Trainer` and `Trainer1D` use Hugging Face `Accelerator`, create output folders, wrap the model/optimizer, and can use multiple workers. Do not instantiate trainers for import-only tests. Use direct loss/sample smoke scripts first.

## FID is slow or dependency-heavy

FID is image-only and belongs to `image-diffusion`. It uses `pytorch-fid` / Inception features, can be slow for `num_fid_samples=50000`, and may require cache/model access. Disable `calculate_fid` for smoke tests.

## Smoke script fails with non-finite loss

First use the bundled defaults. A tiny inspection showed that overly small `timesteps=4` with a linear image schedule can produce NaN loss; `timesteps=8`, `sampling_timesteps=4`, and `beta_schedule='sigmoid'` is the safer image smoke configuration.
