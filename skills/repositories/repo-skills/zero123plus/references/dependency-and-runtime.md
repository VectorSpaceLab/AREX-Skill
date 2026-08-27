# Zero123Plus dependency and runtime reference

Read this before installing or debugging Zero123Plus. This repo is not packaged
as a normal Python distribution; its operating surface is a Diffusers custom
pipeline plus example/demo scripts.

## Backend requirement

- Actual generation requires CUDA and a CUDA-enabled PyTorch build.
- CPU is useful for parser checks, import checks, and the matting helper, but it
  is not a full substitute for Zero123Plus generation.
- The README states the base v1.1 example needs about 5 GB VRAM and the depth
  ControlNet example about 5.7 GB VRAM. Normal generation can be heavier because
  it runs a base pipeline and a ControlNet branch.

## Verified inspection stack

The generated skill was validated against this package combination:

| Component | Version or source | Purpose |
| --- | --- | --- |
| Python | 3.11 | Stable ML package target for this repo |
| torch | 2.0.1 + CUDA 11.8 wheel | GPU inference foundation |
| torchvision | 0.15.2 + CUDA 11.8 wheel | Torch vision dependency |
| numpy | 1.24.4 | Matches the Cog evidence and avoids torch 2.0 / NumPy 2 warnings |
| diffusers | 0.20.2 | Repo-recommended custom pipeline runtime |
| transformers | 4.29.2 | CLIP/text/vision components used by the pipeline |
| huggingface-hub | 0.18.0 | Compatible with the older Diffusers version |
| rembg | 2.0.51 | Background removal in demos and optional postprocessing |
| opencv-contrib-python | 4.11.0.86 | Preprocessing and mask operations |
| segment-anything | git source package | SAM-based demo mask refinement |
| streamlit | 1.22.0 | Source Streamlit demo |
| gradio | 3.50.2 | Source and bundled Gradio demos |
| fire | 0.7.1 | Source Gradio launcher entry point |
| accelerate | 0.24.1 | Optional SDXL helper / Cog evidence |
| pymatting | 1.1.15 | Normal-grid alpha matting helper |
| scipy | 1.15.3 | Normal-grid erosion and matting support |
| cog | 0.22.0 | Cog predictor template import support |

## Representative install recipe

Use an isolated Python 3.11 environment. Install a CUDA-enabled torch wheel
before installing the rest of the stack. Choose the CUDA wheel that matches your
host driver; the verified build used a CUDA 11.8 torch wheel.

```bash
python -m pip install --index-url https://download.pytorch.org/whl/cu118 \
  torch==2.0.1 torchvision==0.15.2

python -m pip install \
  numpy==1.24.4 \
  diffusers==0.20.2 transformers==4.29.2 huggingface-hub==0.18.0 \
  rembg==2.0.51 opencv-contrib-python \
  streamlit==1.22.0 'altair<5' gradio==3.50.2 fire \
  accelerate==0.24.1 requests pymatting scipy cog \
  git+https://github.com/facebookresearch/segment-anything.git
```

If your host needs a newer PyTorch CUDA wheel, re-run the bundled environment
checker after installing it and treat any Diffusers/custom-pipeline drift as a
fresh verification item.

## Model and custom-pipeline loading

The bundled scripts default to local-only Hugging Face cache loading. They use
these public model/custom-pipeline ids by default:

- `sudo-ai/zero123plus-pipeline` for the Diffusers custom pipeline.
- `sudo-ai/zero123plus-v1.1` for the base and depth workflows.
- `sudo-ai/controlnet-zp11-depth-v1` for depth ControlNet.
- `sudo-ai/zero123plus-v1.2` for the normal workflow.
- `sudo-ai/controlnet-zp12-normal-gen-v1` for the normal generator.

Pass `--allow-download` only when the user has approved model/custom-pipeline
network fetches. Otherwise pre-populate the cache before running generation.

## Safe checks

Run the root checker before loading models:

```bash
python scripts/check_zero123plus_env.py --check-only
python scripts/check_zero123plus_env.py --require-cuda
```

For generation-specific parser checks, use each bundled script's `--help` or
`--dry-run`. For deployment-specific checks, use the deployment sub-skill's
bundled Gradio launcher with `--check-only`.
