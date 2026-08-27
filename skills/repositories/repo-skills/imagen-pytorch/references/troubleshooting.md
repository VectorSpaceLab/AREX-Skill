# Troubleshooting

## Use this page first for package-wide failures

This file covers cross-cutting install, import, dependency, T5, and CUDA problems that affect more than one sub-skill. For workflow-specific assertion messages, continue into the nearest sub-skill troubleshooting page.

## 1. Import fails with a missing dependency

**Symptoms**
- `ModuleNotFoundError` for `beartype`, `accelerate`, `datasets`, `einops`, `ema_pytorch`, `kornia`, `pytorch_warmup`, or similar.
- `import imagen_pytorch` fails before you can inspect signatures.

**Likely cause**
- The package or one of its required runtime dependencies is not installed in the current environment.

**Fix**
1. Install the package from PyPI: `pip install imagen-pytorch`.
2. If you are checking a local checkout, ensure the editable install completed successfully.
3. Re-run [scripts/check_imagen_pytorch_env.py](../scripts/check_imagen_pytorch_env.py) to confirm the package imports cleanly.

## 2. Raw text prompts trigger T5 / Hugging Face warnings

**Symptoms**
- Warnings about unauthenticated HF Hub requests.
- Slow first use of `texts=...` paths.
- `Collator`-driven text encoding stalls or fails when offline.

**Likely cause**
- The package is loading the T5 tokenizer/model or downloading cached weights.

**Fix**
- Prefer precomputed `text_embeds` and `text_masks` when you want to avoid downloads.
- If you need raw strings, make sure the environment has network or cached HF assets.
- Route shape and text-encoding details to [data-and-text-conditioning](../sub-skills/data-and-text-conditioning/SKILL.md).

## 3. CUDA is unavailable for realistic generation or training

**Symptoms**
- `torch.cuda.is_available()` is false.
- Sampling, training, or video tasks are unreasonably slow or fail when `.cuda()` is called.

**Likely cause**
- The environment has CPU-only PyTorch, no CUDA driver, or no visible GPU.

**Fix**
- Use the root environment check script with `--check-cuda`.
- For practical image/video generation, switch to a CUDA-capable PyTorch runtime.
- Tiny CPU smoke checks still help with import and config validation, but they do not prove realistic generation quality.

## 4. The `imagen` CLI seems missing or confusing

**Symptoms**
- `imagen` is not on PATH.
- You are looking at `imagen_pytorch.cli.main()` and expecting it to be the entry point.

**Likely cause**
- The console script was not installed, or the wrong function is being inspected.

**Fix**
- The public CLI is the `imagen` console script with `config`, `train`, and `sample` commands.
- Use the CLI quickcheck helper in `configuration-and-cli` if you need command help or config generation.

## 5. A public symbol is not exported from the package root

**Symptoms**
- `from imagen_pytorch import Unet3DConfig` fails.

**Likely cause**
- Some helpers live in their owning module instead of being re-exported.

**Fix**
- Import `Unet3DConfig` and `NullUnetConfig` from `imagen_pytorch.configs`.
- Use [references/api-overview.md](api-overview.md) to confirm the owning module before guessing.

## 6. You need a fast sanity check before deeper debugging

**Use next**
- [scripts/check_imagen_pytorch_env.py](../scripts/check_imagen_pytorch_env.py) for import/version/CUDA/CLI surface checks.
- The sub-skill smoke scripts for tiny workflow-specific checks once you know which route you need.
