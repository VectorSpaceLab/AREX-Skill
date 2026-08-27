# AnyDoor Overview

AnyDoor performs zero-shot object-level image customization with a diffusion
model that combines:

- a ControlNet-style control branch,
- a latent diffusion backbone,
- a DINOv2 image encoder for conditioning,
- mask-aware collage preprocessing,
- optional interactive mask refinement in the demo,
- and a mixed training recipe built from multiple vision datasets.

## Top-level repo map

| Area | Role | Why it matters |
| --- | --- | --- |
| `cldm/` | control-diffusion model code | Defines the AnyDoor control network, the LDM wrapper, and the state-dict loading path. |
| `ldm/` | latent diffusion and encoder utilities | Holds the autoencoder, attention blocks, DINOv2 encoder hook, and diffusion helpers. |
| `datasets/` | dataset classes and preprocessing helpers | Encodes the training/debug input contract and the mask/crop logic used by inference too. |
| `configs/` | model, inference, demo, and dataset YAML files | Contains the placeholder checkpoint and data paths that must be patched. |
| `run_inference.py` | programmatic inference entry | Shows the single-image and VITON-HD generation flow. |
| `run_gradio_demo.py` | local demo entry | Shows the interactive UI, optional mask refinement, and shape-control path. |
| `run_train_anydoor.py` | training entry | Shows the multi-dataset Lightning training recipe. |
| `predict.py` | Cog predictor entry | Shows the prediction API shape and the network download/cache assumption. |
| `scripts/` | shell launchers | Thin launch scripts that benefit from safer bundled wrappers. |
| `iseg/` | optional mask refinement model | Only used when the demo refinement toggle is enabled. |
| `dinov2/` | vendored DINOv2 implementation | Supports the AnyDoor conditioning encoder and its checkpoint path. |

## Core workflow split

1. **Setup and checkpoints**: install the environment, verify CUDA/imports, and
   patch placeholder paths.
2. **Inference and demo**: prepare masks/images and run single-image, batch,
   Gradio, or Cog workflows.
3. **Data and training**: validate dataset layouts, preprocess UVO, inspect
   samples, convert initialization weights, and start training.

## Evidence to trust first

- Public docs in `readme.md` for intended workflows and missing assets.
- Config files in `configs/` for the exact placeholder values and model names.
- Source code in `cldm/`, `ldm/`, and `datasets/` for the real runtime
  signatures and data shapes.
- Safe installed-package inspection from a prepared Python environment for live
  import behavior and backend availability.

## Common assumptions

- The repo is CUDA-oriented for actual generation.
- Checkpoint placeholders are not valid until patched.
- Dataset paths are user-specific and must be supplied by the caller.
- The skill must remain useful even if examples, datasets, or checkpoints are
  absent from the current machine.

## What not to do

- Do not assume training or inference can run without external checkpoints.
- Do not assume the demo can launch if the configs still contain placeholders.
- Do not depend on the source checkout being present when documenting the
  workflow; use bundled references and scripts instead.
- Do not treat generated outputs or review artifacts as runtime skill material.
