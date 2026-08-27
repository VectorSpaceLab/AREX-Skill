# Installation and Smoke Check

Pyramid-Flow has no package metadata file in the inspected snapshot, so the checkout root must be made importable explicitly. Use the repository root on `PYTHONPATH` or run commands from the checkout root; do not assume a normal editable install exists.

## Dependency baseline

The repository's documented runtime baseline centers on the following packages:

- `torch`
- `torchvision`
- `transformers`
- `accelerate`
- `diffusers`
- `einops`
- `opencv-python-headless`
- `imageio`
- `imageio-ffmpeg`
- `sentencepiece`
- `timm`
- `jsonlines`
- `tiktoken`
- `contexttimer`
- `tensorboardX`
- `safetensors`
- `huggingface_hub`

Install the broader UI or analysis extras only when the selected workflow needs them. The repo snapshot also lists `streamlit`, `plotly`, `pandas`, and `python-magic`, but those are not required for the core generation, precompute, or training routes.

## Import-root rule

Because the repo uses top-level modules rather than a packaged install layout, make the checkout root importable before trying any of these imports:

- `pyramid_dit`
- `video_vae`
- `dataset`
- `diffusion_schedulers`
- `trainer_misc`

If one of those imports fails, first check that the checkout root, not a package subdirectory, is visible to Python.

## Quick smoke

Run the root helper first:

```bash
python scripts/check_environment.py --repo PATH_TO_PYRAMID_FLOW
```

Useful variations:

```bash
python scripts/check_environment.py --repo PATH_TO_PYRAMID_FLOW --json
python sub-skills/core-components/scripts/smoke_core_components.py --package-root PATH_TO_PYRAMID_FLOW
```

The first command checks the bundled helper scripts and the core runtime imports. The second command adds the low-level scheduler and tiny VAE smoke checks.

## When to stop and adjust

- If `torch.cuda.is_available()` is false, switch to a CUDA-capable build before expecting generation or training to work truthfully.
- If the helper reports import failures for repo modules, fix `PYTHONPATH` or run from the checkout root before debugging the workflow itself.
- If the repo is being used only for documentation or routing, the bundled helper scripts can still run with `--help` even when checkpoints are missing.
