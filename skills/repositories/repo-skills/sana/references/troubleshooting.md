# Sana cross-cutting troubleshooting

Use this reference for root-level install, import, backend, and CLI triage before routing to a workflow-specific sub-skill. Image, video, training, metrics, conversion, and deployment failures have deeper troubleshooting pages inside the matching sub-skill.

## Safe first checks

```bash
python scripts/check_sana_install.py
python scripts/check_sana_install.py --skip-cli
sana-run --help
sana-upload --help
```

The bundled smoke helper sets `DISABLE_XFORMERS=1` and `DISABLE_FLASH_ATTN=1` for import-only inspection. That isolates optional fused-kernel paths; it does not prove a real generation, training, or benchmark run will work.

## Install and import issues

| Symptom | Likely cause | What to try |
| --- | --- | --- |
| `pip check` reports missing or incompatible packages | The environment was not installed from the repo's pinned dependency set | Reinstall in a clean Python 3.11 environment, then run `python -m pip install -e .` and `python -m pip check`. |
| `mmcv==1.7.2` fails to build/import | `setuptools` is too new or torch was not installed before the build | Pin `setuptools<80`, install the matching torch stack first, then install `mmcv` without build isolation. |
| `diffusion` import fails in fused attention code | Incompatible optional CUDA extension wheel | Disable optional fused paths for inspection, or replace the package with a wheel/source build matching the active torch and CUDA ABI. |
| `torch.cuda.is_available()` is false on a GPU host | CPU-only torch wheel, incompatible driver/runtime, or wrong environment | Verify the active environment and install the CUDA torch wheels that match the target CUDA runtime. |

## Backend expectations

- Sana's practical image/video generation and training workflows are CUDA-oriented.
- CPU-only imports are useful for API, CLI, config, and helper-script inspection only.
- Full generation, video, world-model, streaming, and training claims require a CUDA environment plus task-specific weights, data, and optional kernels.
- SANA-WM streaming `fp4` planning requires Blackwell-class GPUs and Transformer Engine support; `fp8` has separate hardware and package constraints.

## Optional dependency hazards

The following packages can be useful but may break imports if their wheel does not match torch/CUDA:

- `xformers`
- `flash-attn`
- `flash-linear-attention`
- `bitsandbytes`
- `liger_kernel`
- `transformer_engine`

If a smoke import fails inside one of these packages, first prove whether the core route works with the optional path disabled or removed. Do not present that smoke check as validation of the optional accelerated workflow.

## CLI issues

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| `sana-run --help` is missing | The package was not installed with console scripts | Reinstall the package in the active environment and confirm the environment's `bin` directory is on `PATH`. |
| `sana-run` launch fails before submission | Missing SLURM/account/environment variables or invalid command target | Use the evaluation/deployment sub-skill and verify `SANA_SLURM_ACCOUNT`, `SANA_SLURM_PARTITION`, `CONDA_ENV_NAME`, and command quoting. |
| `sana-upload` points at the wrong destination | Repo type, org, repo id, token, or exclude rules are wrong | Treat uploads as remote mutations; inspect with `--help` first and never paste secrets into generated guidance. |

## Network and cache issues

- Many Sana routes fetch model weights, datasets, videos, or benchmark assets from Hugging Face on first real execution.
- Lack of network access or authentication is a runtime precondition failure, not a skill-generation failure, unless the task requires end-to-end execution.
- Record model IDs, dataset IDs, checkpoint paths, and cache expectations explicitly when routing to a sub-skill.

## When to narrow scope

If the environment can only perform import/CLI checks, limit the answer to planning, validation, and troubleshooting. Do not claim verified image/video/training output until a bounded native run has actually executed with the required backend and assets.
