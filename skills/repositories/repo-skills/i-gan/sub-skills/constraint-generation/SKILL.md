---
name: constraint-generation
description: "Headless iGAN constrained generation from color, mask, and edge
  images with safe command planning and input validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# constraint-generation

Use this sub-skill when the user needs iGAN's non-UI constrained generation workflow.
The workflow starts from three image constraints, plans a native command, and explains the legacy backend needed to actually optimize latent vectors.
Keep the agent in command-planning and validation mode unless the user has already provided a compatible iGAN checkout, model artifact, and legacy Theano runtime.

## Read when

- The task mentions the script-without-UI path for iGAN.
- The task supplies a color image, color mask, and edge image.
- The user wants a command for constrained generation without launching PyQt UI controls.
- The user asks about `batch_size`, `n_iters`, `top_k`, or `d_weight` for constrained optimization.
- The user wants to validate constraint image paths, dimensions, or image headers before a native run.
- The user needs to plan the output result grid produced by the headless script.
- The user has an iGAN model file and wants a low-iteration smoke command.
- A previous native run failed while loading Theano, OpenCV, PyQt4, CUDA, cuDNN, or model artifacts.

## Do not use for

- Interactive brush controls, keyboard shortcuts, drawing pad behavior, candidate clicks, sliders, or UI launch details; route to [interactive-ui](../interactive-ui/SKILL.md).
- Downloading, locating, naming, or checking pretrained DCGAN artifacts beyond passing `--model_file`; route setup questions to [model-inference](../model-inference/SKILL.md).
- Projecting an existing image into latent space with `iGAN_predict.py`; route to [image-projection](../image-projection/SKILL.md).
- Training DCGAN models, creating HDF5 datasets, packing trained caches, or predictor training; route to the training/data sub-skill if present.
- Claiming that CPU-only validation proves Theano optimization works; it only proves static command and input contracts.

## Native workflow summary

- The headless script loads a DCGAN model class by `model_type` and an optimizer backend by `framework`.
- Default model selection is `model_name=outdoor_64`, `model_type=dcgan_theano`, and `framework=theano`.
- If `--model_file` is omitted, the native script derives a model path from the model name and model type.
- The script reads `input_color`, `input_color_mask`, and `input_edge` images with OpenCV.
- Each image is resized to the model resolution when its dimensions do not match the model's `npx`.
- Color constraints use the RGB color image.
- Color-mask constraints use the first channel of the color mask after OpenCV loading.
- Edge constraints use the RGB edge image plus the first channel as the edge mask.
- Optimization initializes a batch of latent vectors, runs `n_iters` update steps, keeps the lowest-cost candidates, and writes one visualization image.
- The visualization contains the three input panels followed by selected generated candidates, then is enlarged by a fixed 2x resize in the native script.

## First actions

1. Ask for the three constraint image paths if any are missing.
2. Ask whether the user wants only dry planning or has a prepared legacy runtime for native execution.
3. Validate paths and headers with `scripts/validate_constraint_inputs.py` before constructing a native command.
4. Use `scripts/build_constraint_command.py` to build a deterministic shell command instead of hand-assembling flags.
5. Send model-file preparation questions to [model-inference](../model-inference/SKILL.md) rather than inventing artifact paths.
6. If the user requests GUI interaction, stop this route and use [interactive-ui](../interactive-ui/SKILL.md).

## Bundled references

- [Constraint workflows](references/constraint-workflows.md) gives command recipes, dry-run planning, native execution prerequisites, and output grid math.
- [Data formats](references/data-formats.md) defines image path, channel, mask, dimension, and resize expectations.
- [Troubleshooting](references/troubleshooting.md) maps concrete failure symptoms to causes and recovery steps for this workflow.
- Use [root troubleshooting](../../references/troubleshooting.md) for cross-cutting installation failures when the integrated root skill provides it.

## Bundled scripts

- `scripts/validate_constraint_inputs.py` performs safe existence, readability, header, dimension, and channel-family checks without importing OpenCV, Theano, or PyQt4.
- `scripts/build_constraint_command.py` prints a dry native command plus an output-layout plan; it does not run iGAN, import Theano, download files, train models, or touch the GPU.
- Both scripts support `--help` and are deterministic for the same arguments.
- Prefer the scripts over ad hoc shell snippets because they encode the exact CLI flags and validation assumptions for this workflow.

## Required inputs

- `--input_color`: image containing desired color strokes or regions.
- `--input_color_mask`: mask image indicating where the color image should constrain the generator.
- `--input_edge`: image containing edge or sketch constraints.
- `--model_name`: model configuration name, commonly `outdoor_64` for the documented constraint example.
- `--model_type`: model implementation name; this repo's headless path uses `dcgan_theano`.
- `--framework`: optimizer backend name; this repo's implemented native backend is `theano`.
- `--batch_size`: number of random latent initializations optimized in parallel.
- `--n_iters`: total latent optimization iterations.
- `--top_k`: maximum number of low-cost candidates selected for the output visualization.
- `--d_weight`: discriminator realism cost weight; `0.0` disables discriminator cost in the native optimizer.
- `--output_result`: path for the generated visualization image.

## Safe dry-run recipe

```bash
python scripts/validate_constraint_inputs.py \
  --input-color input_color.png \
  --input-color-mask input_color_mask.png \
  --input-edge input_edge.png \
  --target-size 64

python scripts/build_constraint_command.py \
  --model-name outdoor_64 \
  --input-color input_color.png \
  --input-color-mask input_color_mask.png \
  --input-edge input_edge.png \
  --output-result results/script_result.png \
  --batch-size 4 \
  --n-iters 3 \
  --top-k 4
```

Treat the printed command as a plan until the user confirms the legacy runtime and model artifact are present.
The low-iteration recipe is for smoke planning, not for quality generation.

## Native execution gate

Before running the native headless script, confirm all of the following:

- A compatible Python environment can import the repo's legacy dependencies.
- OpenCV is importable in that environment.
- The Theano backend can compile the model on the requested device.
- A CUDA/cuDNN stack is present when using the documented GPU flags.
- The requested model artifact exists and matches the model name/type.
- The three input images exist and validate under this sub-skill's validator.
- The output directory exists or can be created by the calling workflow.
- The user accepts that the native script may compile Theano functions and use the GPU.

If any gate fails, provide the dry command and a concrete blocker instead of attempting execution.

## Output layout planning

- The native visualization begins with three input panels: color image, color mask, and edge image.
- Generated candidates are concatenated horizontally after those three panels.
- The maximum generated panel count is bounded by `top_k`, but the optimizer may keep fewer candidates after cost thresholding.
- With target size `S`, worst-case pre-resize width is `S * (3 + top_k)` and height is `S`.
- The native script applies a 2x resize before writing, so worst-case final dimensions are `2*S*(3 + top_k)` by `2*S`.
- If `top_k > batch_size`, warn the user because the batch cannot produce more unique candidates than initialized latent vectors.
- For quick smoke checks, set `batch_size` and `top_k` to a small equal value and use low `n_iters`.

## Constraint semantics

- The color mask is a soft numeric mask after normalization to `[0, 1]`, but binary black/white masks are easiest to reason about.
- White or nonzero mask areas increase the effect of the corresponding color image pixels.
- The edge path contributes both an edge image and an edge mask using its first channel.
- Edge pixels should be high-contrast; the optimizer compares HOG features under the edge mask.
- Empty masks make the corresponding constraint weak or ineffective.
- Fully white masks force global matching and can overwhelm the generator.
- If the model is grayscale, generated samples are tiled to RGB for visualization.

## Parameter guidance

- Increase `batch_size` to search more random latent initializations, at higher memory cost.
- Increase `n_iters` for tighter constraint fitting, at higher runtime cost.
- Increase `top_k` only when the output visualization should show more candidate modes.
- Keep `top_k <= batch_size` for meaningful candidate selection.
- Start with `d_weight=0.0` to match the documented script behavior.
- Try small positive `d_weight` only when the discriminator model loads successfully and realism should be weighted against constraint loss.
- Use explicit `--model_file` when the artifact is outside the native default model location.

## Troubleshooting routing

- Missing image path, mismatched dimensions, unsupported headers, or weak masks: use [Data formats](references/data-formats.md) and the validator.
- Missing model artifacts, unknown model names, or sample-generation smoke checks: use [model-inference](../model-inference/SKILL.md).
- Python2-era Theano, CUDA, cuDNN, OpenCV, PyQt4, Lasagne, or Fuel failures: use [Troubleshooting](references/troubleshooting.md) first, then root troubleshooting if needed.
- No display, brush behavior, or candidate thumbnail UI issues: route to [interactive-ui](../interactive-ui/SKILL.md).
- `iGAN_predict.py` solver, AlexNet, or `x -> z` reconstruction issues: route to [image-projection](../image-projection/SKILL.md).

## Verification stance

- This sub-skill can be verified statically with helper `--help`, command generation, and image header validation.
- Native constrained generation remains an optional CUDA/Theano/model case.
- The native candidate is the headless script with the documented sample input contract.
- Do not report native generation as verified unless the command actually writes the requested output image in a compatible runtime.
- Keep any unavailable legacy backend as an explicit known gap in the parent verification report.
