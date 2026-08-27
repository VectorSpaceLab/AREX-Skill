# Constraint generation workflows

This reference replaces the need to reopen the original headless script when planning iGAN constrained generation. Use it with the bundled scripts in `../scripts/`.

## Capability boundary

This workflow plans and validates headless generation from three constraint images:

- a color image that stores desired RGB values,
- a color mask that selects where color should matter,
- an edge image that stores sketch/edge constraints and also supplies the edge mask through its first channel.

It does not download models, launch the GUI, train models, or project images into latent space. Route those tasks to the sibling sub-skills named in `../SKILL.md`.

## Dry planning sequence

Run validation first:

```bash
python scripts/validate_constraint_inputs.py \
  --input-color input_color.png \
  --input-color-mask input_color_mask.png \
  --input-edge input_edge.png \
  --target-size 64
```

Then build a command without executing it:

```bash
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

The command builder prints a shell-safe command and an output-layout plan. It never imports the native iGAN modules and never uses the GPU.

## Native command shape

A native run has this shape after the environment and model artifact are ready:

```bash
THEANO_FLAGS='device=gpu0,floatX=float32,nvcc.fastmath=True' \
python iGAN_script.py \
  --model_name outdoor_64 \
  --model_type dcgan_theano \
  --framework theano \
  --input_color input_color.png \
  --input_color_mask input_color_mask.png \
  --input_edge input_edge.png \
  --output_result results/script_result.png \
  --batch_size 4 \
  --n_iters 3 \
  --top_k 4 \
  --d_weight 0.0
```

Only run it from a prepared iGAN checkout or another workspace containing the same script/module layout. Treat this as a GPU/Theano action, not a harmless parser check.

## Native execution prerequisites

Before running the command, confirm:

1. The chosen Python can import OpenCV as `cv2`.
2. The chosen Python can import Theano and compile Theano functions.
3. The optimizer backend module for `--framework theano` is available.
4. The model implementation for `--model_type dcgan_theano` is available.
5. The model artifact exists and matches the chosen model configuration.
6. The requested device in `THEANO_FLAGS` is valid for the host.
7. The output directory exists or the caller will create it before execution.
8. The user accepts possible CUDA/cuDNN compilation and GPU memory use.

If any item is unresolved, do not run the native command. Return the dry command plus the blocker.

## Model flags

- `--model_name`: names the model configuration. `outdoor_64` is the documented headless example.
- `--model_type`: defaults to `dcgan_theano`.
- `--model_file`: optional explicit artifact path. If omitted, the native script derives a path from `model_name` and `model_type`.
- `--framework`: defaults to `theano`, which loads the Theano constrained optimizer.

Model acquisition and artifact URL planning are owned by the model-inference sub-skill. Use this workflow only to pass the chosen artifact into the headless generation command.

## Constraint flags

- `--input_color`: color target image.
- `--input_color_mask`: mask for color constraints.
- `--input_edge`: edge/sketch constraint image.
- `--output_result`: output visualization image path.

The native script reads every image through OpenCV's color-read mode and resizes each image independently to the model's `npx` resolution. The validator is stricter by default about matching dimensions because independent resize can hide accidental file mixups.

## Optimization flags

- `--batch_size`: number of latent vectors optimized in parallel.
- `--n_iters`: number of optimization updates.
- `--top_k`: maximum number of displayed low-cost candidates.
- `--d_weight`: discriminator realism term weight.

Use small values for smoke checks:

```bash
python scripts/build_constraint_command.py \
  --model-name outdoor_64 \
  --input-color input_color.png \
  --input-color-mask input_color_mask.png \
  --input-edge input_edge.png \
  --output-result smoke_result.png \
  --batch-size 2 \
  --n-iters 1 \
  --top-k 2
```

Use production-like values only after a smoke run succeeds. The documented defaults are `batch_size=64`, `n_iters=100`, and `top_k=16`.

## Output-layout plan

The native script writes a single visualization image:

1. color input panel,
2. color-mask panel,
3. edge input panel,
4. selected generated candidate panels.

The candidate panels are concatenated horizontally, not in a multi-row thumbnail grid. The maximum panel count is `3 + top_k`, but the optimizer can return fewer candidates when its internal cost threshold selects less than `top_k` results.

For target size `S` and maximum candidate count `K`:

- worst-case pre-resize width: `S * (3 + K)`,
- worst-case pre-resize height: `S`,
- final width after native 2x resize: `2 * S * (3 + K)`,
- final height after native 2x resize: `2 * S`.

Example for `S=64`, `top_k=4`:

- pre-resize: `448 x 64`,
- final visualization: `896 x 128`.

Example for `S=64`, `top_k=16`:

- pre-resize: `1216 x 64`,
- final visualization: `2432 x 128`.

## Recommended workflow decisions

- Keep `top_k <= batch_size`; otherwise warn that no more candidates can be selected than the number of initialized latent vectors.
- Use `n_iters=1..5` only for smoke tests.
- Use the model's native size, commonly 64 for the documented models, unless the model-inference sub-skill confirms another size.
- Validate all three image headers even though OpenCV would resize at runtime.
- Do not pass GUI screenshots as masks unless the user confirms they encode mask intensity in a channel.
- Keep output filenames outside input directories when iterating to avoid confusing input and output files.

## JSON command output

For machine-readable planning, use:

```bash
python scripts/build_constraint_command.py \
  --format json \
  --model-name outdoor_64 \
  --input-color input_color.png \
  --input-color-mask input_color_mask.png \
  --input-edge input_edge.png \
  --output-result results/script_result.png \
  --batch-size 4 \
  --n-iters 3 \
  --top-k 4
```

The JSON includes the argument vector, shell command, Theano flags, and layout estimate. It is suitable for verification scripts because key ordering is stable.

## Failure handling

If validation fails, report the failing path and reason exactly as printed. If command building fails, fix invalid numeric flags before discussing Theano. If native execution fails, use `troubleshooting.md` to separate dependency, model artifact, image decoding, and GPU/compiler causes.
