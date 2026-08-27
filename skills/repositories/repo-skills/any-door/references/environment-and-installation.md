# Environment and Installation

AnyDoor is an older torch-based repository. The safest supported setup is a
Python 3.8 environment with CUDA-capable PyTorch and the runtime packages used
by the repo scripts.

## Recommended install order

1. Create an isolated Python 3.8 environment.
2. Install a CUDA-capable PyTorch stack that matches the host driver.
3. Install the repo runtime dependencies.
4. Install dataset extras only if you need training or dataset debugging.
5. Verify imports and CUDA before trying generation.

## Supported install patterns

| Pattern | When to use | Notes |
| --- | --- | --- |
| Conda environment | Preferred for compiled ML stacks | Best fit for this repo because torch, torchvision, OpenCV, and related packages are involved. |
| Existing private venv | Acceptable when Conda is unavailable | Keep it isolated and avoid mutating a user-owned environment unless approved. |
| CPU-only inspection | Only for support workflows | Useful for imports, config parsing, and dataset helper checks, but not for actual image generation. |

## Evidence-backed Python and backend choice

- `environment.yaml` specifies Python 3.8.
- `readme.md` and `cog.yaml` show a CUDA-oriented generation workflow.
- The repo’s runtime model code expects torch, torchvision, OpenCV, and CUDA
  availability for generation paths.
- `xformers` is optional; the attention code has a fallback when it is absent.

## Base dependency groups

### Required for core inspection and most workflows

- `torch`, `torchvision`
- `einops`
- `omegaconf`
- `albumentations`
- `opencv-python-headless` or the equivalent OpenCV wheel
- `pillow`
- `pytorch-lightning`
- `safetensors`
- `gradio`
- `open-clip-torch`
- `transformers`
- `fvcore`
- `submitit`
- `timm`
- `torchmetrics`
- `sentencepiece`

### Additional dataset/training helpers

- `pycocotools`
- `lvis`
- `panopticapi`

### Optional

- `xformers` for memory-efficient attention, if a compatible wheel exists.
- `share` for the source weight-conversion helper; if unavailable, document it
  as a source-side limitation rather than blocking all repo usage.

## Safety expectations

- Do not install into Conda `base`.
- Do not mutate a user-owned environment unless the user explicitly allowed it.
- Do not treat a CPU import as proof of CUDA generation readiness.
- Do not install the full training/data stack if you only need inference or
  environment inspection.

## What the preflight should prove

Before routing to inference or training, the environment checker should confirm:

- the repo layout is present,
- the key modules import,
- `torch.cuda.is_available()` is true on a CUDA host,
- a minimal CUDA allocation succeeds,
- optional `xformers` status is known,
- placeholder checkpoint paths are still visible and therefore need patching.

## When to stop and read more

Read `references/checkpoints-and-configs.md` after the environment is ready.
Read `references/troubleshooting.md` if any import, wheel, or CUDA smoke check
fails.
