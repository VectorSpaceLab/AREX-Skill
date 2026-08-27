# Cross-cutting troubleshooting

## Purpose

Use this when xTuring fails before you reach a narrower data, model, training, CLI/API, or evaluation workflow. Task-specific fixes live in the nearest sub-skill troubleshooting page.

## Install and import failures

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'xturing'` | The package is not installed in the active environment | Install from the repository root with `pip install -e .` and rerun `scripts/check_xturing_environment.py`. |
| `xturing` CLI is missing or cannot be found | The console script is not on `PATH` or the environment is not the one that installed xTuring | Use the environment that installed xTuring, then rerun the environment check script. |
| `xturing` imports but submodules fail immediately | A required dependency from `pyproject.toml` is missing or broken | Inspect the failing sub-skill troubleshooting page and rerun the environment check script. |

## Optional dependency and backend issues

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `The anthropic SDK is required for ClaudeTextGenerationAPI...` | Claude generation needs the `anthropic` package | Install the provider package or use a different API wrapper. |
| `bitsandbytes` CUDA setup errors or quantized model import failures | The CUDA runtime, wheel, or library path does not match the installed bitsandbytes build | Use the CUDA-matched wheel for your runtime, make sure the CUDA library is visible to the process, or switch to a non-quantized workflow. |
| `DeepSpeed is required for optimizer 'cpu_adam'` or `use_deepspeed=True requires DeepSpeed` | The optional DeepSpeed backend is missing | Install `deepspeed` or disable the DeepSpeed/CPU-Adam path. |
| `To run int8 or k-bits model on cpu, please install the intel-extension-for-transformers package.` | CPU INT8 is routed through ITRex | Install `intel-extension-for-transformers` or use a CUDA-capable non-CPU INT8 path. |
| `WARNING: CUDA is not available, using CPU instead` | The installed PyTorch build cannot see a CUDA device | Use the CPU-safe workflows or install a CUDA-capable PyTorch stack before trying LoRA INT8/K-bit or GPU training. |

## Data and workflow gaps

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `Text2ImageDataset is not implemented` | Image data is routed to a placeholder class | Do not use this package for image generation data workflows. |
| `StableDiffusion` raises `NotImplementedError` | The placeholder model is registered but not usable | Choose a supported causal model family instead. |
| `xturing api` loads but requests fail with 503 | The service model has not been loaded yet | Load a valid model directory with `xturing api -m <model_dir>` or use the CLI/model skill to create a saved checkpoint first. |

## How to proceed

- If the issue is about dataset shape, switch to `sub-skills/data-prep-and-generation/SKILL.md`.
- If the issue is about model loading or backend capability, switch to `sub-skills/models-and-inference/SKILL.md`.
- If the issue is about fine-tuning or DPO, switch to `sub-skills/training-and-alignment/SKILL.md`.
- If the issue is about HTTP routes or the playground, switch to `sub-skills/cli-api-ui/SKILL.md`.
- If the issue is about perplexity or adapter results, switch to `sub-skills/evaluation/SKILL.md`.
