# Evaluation and Benchmark Reference

## When to read

Read this when preparing RVM prediction directories, selecting LR/HR metric
scripts, interpreting metric names, or explaining synthetic evaluation data and
speed benchmarks.

## Expected prediction and ground-truth tree

Both prediction and true roots must have matching nested directories:

```text
videomatte_512x288-or-1920x1080/
  videomatte_motion/
    0000/
      pha/
        0000.png
      fgr/
        0000.png
  videomatte_static/
    0000/
      pha/
        0000.png
      fgr/
        0000.png
```

The original LR/HR evaluators iterate datasets and clips under `pred-dir`, then
read matching `pha` and optional `fgr` frames from `true-dir`. Prediction and
ground truth frame filenames must match exactly.

## Low-resolution evaluator

The LR evaluator is CPU/NumPy/OpenCV based. Default metrics:

- `pha_mad`
- `pha_mse`
- `pha_grad`
- `pha_conn`
- `pha_dtssd`
- `fgr_mad`
- `fgr_mse`

Source CLI shape:

```bash
python evaluate_lr.py \
  --pred-dir PATH_TO_PREDICTIONS/videomatte_512x288 \
  --true-dir PATH_TO_GROUND_TRUTH/videomatte_512x288 \
  --num-workers 48
```

It writes an Excel workbook named after the prediction root basename inside the
prediction root.

## High-resolution evaluator

The HR evaluator is designed for high-resolution evaluation and moves alpha
tensors to CUDA. It uses Kornia for gradient filtering. Default metrics:

- `pha_mad`
- `pha_mse`
- `pha_grad`
- `pha_dtssd`
- `fgr_mse`

It does not provide a CPU fallback in the source script; use a CUDA environment
or choose LR/tiny evaluation for CPU validation.

## Bundled tiny LR evaluator

The bundled script computes a safe JSON summary and performs stricter frame
matching before reading data:

```bash
python scripts/rvm_evaluate_lr_tiny.py \
  --pred-dir pred/videomatte_512x288 \
  --true-dir true/videomatte_512x288
```

Default bundled metrics are `pha_mad`, `pha_mse`, `pha_dtssd`, `fgr_mad`, and
`fgr_mse`. It omits the heavier gradient/connectivity implementations so it can
serve as a small validation helper rather than a full paper evaluator.

## Metric meanings

- MAD: mean absolute difference scaled by `1e3`.
- MSE: mean squared error scaled by `1e3`.
- GRAD: Gaussian-gradient error, scaled as in matting benchmarks.
- CONN: connectivity error across alpha thresholds.
- dtSSD: temporal difference SSD, comparing frame-to-frame alpha changes and
  scaled by `1e2`.
- Foreground metrics apply only where ground-truth alpha is nonzero.

## Synthetic evaluation composite scripts

The repository includes four compositing script families for building evaluation
sets from matte foreground/alpha data and static or video backgrounds:

- VideoMatte with background images.
- VideoMatte with background videos.
- ImageMatte with background images.
- ImageMatte with background videos.

They take matte/background roots, sample counts, frame counts, resolution or
resize, output directory, seed/extension options, and then write `fgr`, `pha`,
`bgr`, and `com` directories. The ImageMatte scripts use documented random
seeds for distinction/adobe static/motion variants. The video-background
variants read selected background video names and require video-decoding
support.

Treat these as reference workflows by default: they require large external
datasets, may create many files, and some use symlinks for repeated static
background frames.

## Speed benchmark caveats

The README speed table reports tensor throughput measured by a CUDA-only speed
script with synthetic input, JIT scripting/freezing, and 1000 iterations. It is
not the same as end-to-end video conversion throughput.

Important distinctions:

- Tensor benchmark excludes video decode/encode and most disk IO.
- The converter performs Python media IO and can be much slower.
- FP16 speed depends on GPU architecture; older GPUs may not benefit.
- Published HD and 4K numbers use specific downsample ratios and batch/chunk
  conditions.

For a safe model API check, use the model-api sub-skill's smoke script. For a
real benchmark, run a deliberately scoped CUDA experiment and report hardware,
dtype, resolution, downsample ratio, chunk size, warmup, and whether media IO is
included.
