# Zero123Plus root troubleshooting

Use this for cross-cutting failures before routing into a sub-skill. For
workflow-specific details, read:

- [`../sub-skills/generation/references/troubleshooting.md`](../sub-skills/generation/references/troubleshooting.md)
- [`../sub-skills/deployment/references/troubleshooting.md`](../sub-skills/deployment/references/troubleshooting.md)

## First response checklist

1. Run `python scripts/check_zero123plus_env.py --check-only`.
2. If the user wants a real generation or demo run, run the same checker with
   `--require-cuda`.
3. Confirm whether model/custom-pipeline downloads are approved. Bundled scripts
   do not fetch missing models unless `--allow-download` is passed.
4. Route to generation for model/camera/matting issues and to deployment for
   Streamlit, Gradio, Docker, or Cog issues.

## CUDA is missing

**Symptom:** `torch.cuda.is_available()` is false, a script falls back to CPU, or
model loading fails at `.to('cuda')`.

**Likely cause:** CPU-only PyTorch, no visible NVIDIA device, container GPU
passthrough missing, or an incompatible driver/wheel pair.

**Recovery:** Install a CUDA-capable torch/torchvision wheel, move to a GPU
runtime, or stop if the task requires actual generation. CPU-only execution is
not a truthful validation of Zero123Plus generation.

## NumPy / PyTorch warning

**Symptom:** torch 2.0.1 emits warnings about modules compiled against NumPy 1.x
when NumPy 2.x is installed.

**Recovery:** Use the repo/Cog-compatible NumPy 1.24.x line. The inspection run
used `numpy==1.24.4`.

## Diffusers or Hugging Face Hub drift

**Symptom:** custom pipeline loading or scheduler setup fails after installing a
newer package set.

**Likely cause:** The repo evidence targets `diffusers==0.20.2`; newer
`huggingface-hub` releases can break older Diffusers import assumptions.

**Recovery:** Reproduce with `diffusers==0.20.2`, `transformers==4.29.2`, and
`huggingface-hub==0.18.0` before changing model code.

## Model cache or network failures

**Symptom:** a bundled script fails immediately with a local-files-only or cache
miss message.

**Recovery:** Either pre-populate the Hugging Face cache or rerun with
`--allow-download` after the user approves network/model fetches. Do not silently
turn on downloads in CI or offline environments.

## Normal postprocess dependencies are missing

**Symptom:** normal generation works with `--skip-postprocess` but fails during
matting.

**Recovery:** Install `pymatting` and `scipy`, or keep raw color/normal grids
with `--skip-postprocess`. The CPU synthetic postprocess smoke passed in the
inspection environment.

## Demo/deployment failures

**Symptom:** Streamlit/Gradio/Cog launch fails, SAM checkpoint is missing,
`rembg` downloads a model, `pget` is missing, or a container cannot find weights.

**Recovery:** Use the deployment sub-skill. Treat SAM checkpoints, rembg/ONNX
models, Cog archives, and Hugging Face models as separate download approvals.
