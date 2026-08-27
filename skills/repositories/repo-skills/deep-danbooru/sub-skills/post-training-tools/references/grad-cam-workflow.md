# Experimental Grad-CAM workflow

## Status and command shape

The repository labels `grad-cam` **Experimental feature**. It computes input
gradients for selected output tags and writes qualitative images; it is not a
validated explanation method, causal attribution, model-quality metric, or
replacement for ordinary evaluation.

```text
deepdanbooru grad-cam PROJECT_PATH TARGET_PATH [OUTPUT_PATH] [--threshold FLOAT]
```

- `PROJECT_PATH` is an existing project directory. The command loads both the
  model and tags from it; unlike `evaluate`, there is no direct model/tags
  override.
- `TARGET_PATH` is an existing image file or directory.
- `OUTPUT_PATH` is an output directory, defaulting to `.`. The command creates
  it when absent.
- `--threshold` is a floating-point selection threshold, default `0.5`.
  A tag is selected when its score is **greater than or equal to** the
  threshold. There is no `--verbose` option.

Use a disposable output directory. Existing same-named files may be replaced.
A safe first run uses one small local image and the same threshold used by
ordinary evaluation:

```bash
mkdir -p artifacts/grad-cam
deepdanbooru grad-cam PROJECT IMAGE artifacts/grad-cam --threshold 0.5
```

## Inputs and project prerequisites

The loader reads `project.json`, gets its `model` value, and searches for
`model-{model}.keras`, then `model-{model}.h5`. It reads one tag per non-empty
line from `tags.txt`. The tag sequence must align with the model output vector;
check this before interpreting a map. The model must expose an image input with
height at `input_shape[1]` and width at `input_shape[2]`.

A file target processes exactly that file. A directory target is recursively
searched for PNG, JPG, JPEG, and GIF files with case-insensitive patterns, then
natural-sorted. Each image is decoded, resized with aspect-ratio preservation,
edge-padded to model dimensions, and normalized to `[0, 1]`. Decode support is
runtime-dependent: the package uses TensorFlow PNG decoding and TensorFlow I/O
for WebP fallback, so a Pillow-readable file is not by itself proof that
DeepDanbooru can decode it.

## Selection and output tree

For each source image, the command creates a directory beneath the output path
named after the input basename without its extension:

```text
OUTPUT_PATH/
└── image_name/
    ├── input.png
    ├── result-TAG.png
    └── result-TAG-masked.png
```

`input.png` is the normalized/padded input converted back to 8-bit RGB. For
each tag with score `>= threshold`, the implementation prints the selected tag
and writes:

- `result-TAG.png`: absolute input gradients, clipped at the 1st/99th
  percentiles, normalized, then median-filtered with SciPy size `10`.
- `result-TAG-masked.png`: the input multiplied by the per-pixel maximum
  gradient mask.

In both filenames, `:` and `/` are replaced with `_`; other unusual characters
are not comprehensively sanitized. If no output score reaches the threshold,
`input.png` may be the only file. That is an expected no-selection case, not
proof that gradient computation crashed. The printed `Tags of ...` block and
result filenames should agree.

The source obtains predictions with the Keras model, then uses
`tf.GradientTape` with a one-hot mask for each selected output. Grad-CAM can be
slow on CPU because each selected tag needs gradient work. GPU may be faster in
a separately prepared environment, but GPU availability and speed are optional
and unverified; CPU is the correctness baseline.

## Safe interpretation and routing

1. Run ordinary inference first with
   [Inference and evaluation](../../inference-evaluation/SKILL.md), using the
   same image and threshold.
2. Confirm the project model, tags, and target decode before the visualization.
3. Inspect that `input.png` exists, then compare selected tags and generated
   names. Treat bright regions as qualitative signals only.
4. If the model is missing, stale, or must be retrained, use
   [Model training](../../model-training/SKILL.md), not this workflow.
5. Do not import `deepdanbooru.gradcam` as a general API: the legacy module
   invokes a test at import time and is separate from the CLI implementation.
