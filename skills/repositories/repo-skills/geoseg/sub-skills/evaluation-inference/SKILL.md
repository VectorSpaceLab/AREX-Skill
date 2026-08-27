---
name: evaluation-inference
description: "Evaluate GeoSeg benchmark tiles and run CUDA inference on UAVid
  sequences or large remote-sensing images with checkpoint-aware TTA and mask
  output handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Evaluation and inference

Use this route after selecting a compatible GeoSeg config and checkpoint. Run
the bundled preflight before any GPU entry point. For actual execution, use the
bundled root wrapper [`run_geoseg_entrypoint.py`](../../scripts/run_geoseg_entrypoint.py)
with an explicit user-supplied GeoSeg checkout; it preserves the checkout as
the process root while keeping the skill itself self-contained. This sub-skill
is reference-only for the GPU entry points: the checkout contains no datasets
or model checkpoints, and all three routes require CUDA.

## Choose one route

- **Benchmark tile evaluation:** the Vaihingen, Potsdam, or LoveDA tile
  evaluator entry point. These load `config.test_dataset`, predict each
  prepared tile, optionally compute `Evaluator` metrics, and write PNG masks.
  See [CLI reference](references/cli-reference.md) and [tile
  workflow](references/workflows.md#1-benchmark-tile-evaluation).
- **UAVid sequence inference:** the UAVid sequence entry point. Use when the
  input is a UAVid-style directory of sequences containing `Images/`; it writes
  one `Labels/` directory per sequence. See [the UAVid
  workflow](references/workflows.md#2-uavid-sequence-inference).
- **Huge-image inference:** the huge-image entry point. Use for a flat folder
  of `.tif`, `.png`, or `.jpg` images. It bottom/right pads each image,
  predicts non-overlapping tiles in row-major order, stitches them, crops back
  to the original height and width, and writes one output per input image. See
  [the huge-image workflow](references/workflows.md#3-huge-image-inference).

Do not use a tile evaluator for unsplit huge images, and do not pass a UAVid
sequence root to the flat-folder huge-image route.

## Required preflight

1. Read the selected config and verify `num_classes`, model family, dataset
   roots, and the checkpoint convention
   `os.path.join(config.weights_path, config.test_weights_name + ".ckpt")`.
   Relative config paths are resolved from the process working directory.
   The usual checkpoint locations are `model_weights/<dataset>/...`; these
   files are external and absent from the checkout.
2. Prepare the input layout described in [the output/workflow references](references/workflows.md)
   and use the matching dataset/config. Vaihingen and Potsdam use six classes;
   LoveDA uses seven; UAVid uses eight.
3. Confirm a CUDA-capable PyTorch runtime. The verified inspection runtime used
   Python 3.8, torch 2.0.1+cu118, and an NVIDIA A100 (compute capability 8.0).
   CPU is suitable for static checks and preprocessing only, not truthful
   execution of these entry points.
4. Choose TTA deliberately. Omit `-t` for no TTA; use `-t lr` for the script's
   horizontal+vertical flip wrapper or `-t d4` for its script-specific
   multiscale/flip composition. Do not pass the literal string `None`.
5. Decide indexed versus RGB output. Tile evaluators accept `--rgb`; UAVid
   sequence inference always emits the UAVid palette, and huge-image inference
   always maps the selected `-d` palette. Validate the mapping in
   [output formats](references/output-formats.md) before submitting masks.

A safe, dependency-free preflight is the operational first step when its
checks match the workflow. Run it from the GeoSeg repository root (or replace
paths with absolute paths):

```bash
python <path-to-this-skill>/sub-skills/evaluation-inference/scripts/validate_inference_inputs.py \
  --mode huge --image-path /abs/data/vaihingen/test_images \
  --config /abs/GeoSeg/config/vaihingen/dcswin.py \
  --output-path /abs/results/vaihingen/dcswin_huge \
  --dataset pv --check-padding
```

It does not import GeoSeg, load data, download anything, test CUDA, create
output directories, or prove checkpoint tensor compatibility. Treat its
warnings as a prompt to inspect the references, not as permission to run
without a checkpoint. The exact original entry-point flags and defaults are
preserved in [CLI reference](references/cli-reference.md); execute those flags
through the future wrapper or a user-supplied checkout path only after this
preflight succeeds.

## Sibling routes

- Prepare or repair dataset folders and masks with
  [data-preparation](../data-preparation/SKILL.md).
- Select a model, class count, and config/checkpoint pairing with
  [model-and-config](../model-and-config/SKILL.md).
- Resolve dependency, CUDA, data, output, and shape failures with
  [troubleshooting](references/troubleshooting.md).
