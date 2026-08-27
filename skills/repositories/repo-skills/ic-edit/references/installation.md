# Installation

## Purpose

Use this reference before running the bundled helpers. It captures the package set that matched the inspected ICEdit workflows.

## Environment shape

- Python 3.11
- CUDA-capable torch build
- One environment is enough for the inspected workflows when it includes both the inference/demo stack and the training support libraries.

## Base editing stack

Install the packages that support the normal inference and Gradio demo paths:

```bash
python -m pip install \
  accelerate \
  diffusers==0.33.0 \
  gradio \
  numpy \
  peft \
  protobuf \
  sentencepiece \
  spaces \
  torch==2.7.0 \
  torchvision \
  transformers==4.51.3 \
  gguf
```

## Training support libraries

Add the packages that the inspected training code imports directly:

```bash
python -m pip install \
  lightning \
  datasets==3.6.0 \
  opencv-python \
  prodigyopt \
  pyyaml \
  wandb
```

`pyyaml` is required by both the launcher and the nested training entrypoints; it is listed explicitly in `train/requirements.txt`.

## Training checkout versus standalone helper

The launcher is a standalone, dry-run-capable helper. It does not copy or package the training source. A real launch is checkout-dependent: the checkout must contain `train/src/train/` and `train/train/config/`. The helper runs with `cwd=<ICEdit checkout>/train` and `PYTHONPATH=<ICEdit checkout>/train`, matching the source checkout wrappers.

MoE training has one additional checkout dependency. `train/src/train/train_moe.py` prepends the checkout-vendored `icedit/` fork of diffusers/peft; that package is not supplied by this helper or by pip. Use `--mode moe` only from a checkout containing `icedit/` and pass `--repo-root` when auto-discovery is unavailable.

Without a usable checkout, the helper can still inspect an explicitly supplied YAML: dry-run reports missing source, vendored package, and local inputs as warnings. `--execute` refuses to invoke `accelerate` until those checkout requirements and clearly local resources are present.

## CUDA note

- The inspection environment resolved `torch 2.7.0+cu126` and passed a minimal CUDA tensor check.
- If your resolver lands on a CPU-only wheel, replace it with a CUDA build before using the primary workflows.
- The repository does not provide a CPU substitute for the main editing or training routes.
- `datasets==3.6.0` matched the inspected training helpers after a broader resolver pass selected an incompatible older release.

## Checkout-only paths

- Normal inference and Gradio use the standalone helpers in this skill tree. They still download default Hub weights unless local paths are supplied.
- MoE requires an ICEdit checkout with `icedit/` and `--repo-root <ICEdit checkout>`.
- Training requires checkout directories `train/src` and `train/train/config`; neither training source nor those configs is bundled in this skill.

## Recommended post-install check

Run the bundled environment checker from any cwd using its absolute path:

```bash
python /path/to/ic-edit-skill/scripts/check_icedit_env.py
```

For the vendored-path check, pass `--repo-root /path/to/ICEdit --check-vendored`.


## Not required by the inspected code paths

- `torchao`
- `jupyter`

Those packages appear in the repo's broader training requirements, but they were not required by the bundled helper checks for the selected workflows.
