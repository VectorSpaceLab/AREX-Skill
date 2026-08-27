# Cross-Cutting Troubleshooting

Use this for failures that affect multiple sd-scripts workflows. Workflow-specific troubleshooting lives in each sub-skill.

## Installation and Imports

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ModuleNotFoundError: torch` or `diffusers` | Requirements were not installed in the active environment | Install workflow dependencies in the environment that will run sd-scripts; install PyTorch first with the CUDA/CPU wheel matching the machine. |
| `pip install -r requirements.txt` fails on torch | PyTorch is intentionally installed separately | Install `torch` and `torchvision` from the official wheel index for the platform, then install requirements. |
| `accelerate: command not found` | Accelerate missing or wrong environment active | Install requirements in the active environment and run `python -m accelerate.commands.config` or `accelerate config`. |
| `fp16 mixed precision requires a GPU` | Accelerate config selected fp16 without visible GPU | Re-run `accelerate config`, choose CPU/no mixed precision, or run on a GPU-visible machine. |
| xformers import or ABI error | xformers wheel incompatible with torch/Python/CUDA | Prefer `--sdpa` when available, or install xformers from the matching PyTorch/CUDA index. |

## Hardware and Backend

- Match PyTorch CUDA wheels to the driver and GPU architecture. New NVIDIA architectures often need recent CUDA wheels.
- Do not assume `nvidia-smi` CUDA version means a toolkit is installed; pip wheels include runtime libraries, while source builds need compilers/toolkit.
- If GPU is unavailable, avoid promising full training or high-resolution generation. Use command planning and read-only validation instead.
- For memory errors, reduce resolution, batch size, VAE batch size, network dimension, cache strategy, or use gradient checkpointing/SDPA/fp8/block swap where supported.

## Execution Safety

- Training, generation, caching, model conversion, LoRA extraction, and checkpoint merge operations can write large files and run for a long time.
- Always confirm output paths and avoid overwriting input model files.
- Treat model downloads, Hugging Face access, private datasets, and credentials as explicit user-managed prerequisites.
- Use bundled validators and command builders before running heavyweight workflows.

## Model-Family Mismatch

| Mismatch | Signal | Fix |
| --- | --- | --- |
| SD2 v-prediction without `--v_parameterization` | Brown or unusable images | Add both `--v2` and `--v_parameterization` for those checkpoints. |
| SDXL command uses SD1/2-only flags | Load or argument errors | Use SDXL scripts and SDXL conditioning options. |
| FLUX/Chroma command uses SD LoRA module | Missing keys or incompatible network | Use FLUX-family script and `networks.lora_flux`; Chroma omits CLIP-L and requires Chroma-specific guidance options. |
| LoRA applied to wrong base family | Shape/key mismatch | Confirm adapter metadata, base model family, and merge/generation script family before applying. |

## When to Defer Native Execution

Skip native execution and record the skip when a check requires model weights, GPU, long training, large checkpoint writes, network downloads, private credentials, or destructive output changes. Prefer synthetic validator cases and metadata checks for publication-quality skill verification.
