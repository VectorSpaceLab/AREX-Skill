# Evaluation Troubleshooting

## Empty prediction directory

The original evaluators assume at least one dataset/clip result. An empty
prediction root can fail later when creating workbook sheets or reading
`results[0]`.

Recovery: confirm the root contains `dataset/clip/pha/*.png` before running full
evaluation. The bundled tiny evaluator exits early with a clear error.

## Prediction and ground truth frames do not match

**Symptoms:** `FileNotFoundError`, OpenCV returns `None`, or metrics silently
compare an unintended subset in custom scripts.

**Recovery:** Match dataset names, clip names, subdirectories, frame basenames,
and extensions exactly. Use zero-padded frame names. The bundled tiny evaluator
checks exact frame-name equality for `pha/` and `fgr/` when needed.

## Foreground metrics fail

Foreground metrics need matching `fgr/` frames and a non-empty ground-truth alpha
mask. If the alpha mask is empty for a frame, foreground metric aggregation can
be undefined or skipped.

Recovery: include `fgr/` predictions and truth only when foreground metrics are
requested, or restrict metrics to alpha-only names.

## OpenCV, XlsxWriter, or Kornia import errors

- LR source evaluator needs OpenCV, NumPy, XlsxWriter, and tqdm.
- HR source evaluator also needs PyTorch CUDA and Kornia.
- The bundled tiny evaluator can read images through OpenCV or Pillow and does
  not write Excel by default.

Install only the dependencies needed for the selected evaluation path.

## HR evaluator fails on CPU

The HR source script calls `.cuda()` directly for alpha tensors and gradient
filters. It is not a CPU fallback.

Recovery: use a CUDA environment for HR metrics, or run LR/tiny evaluation for
CPU-side plumbing validation. Do not claim HR metric parity from a CPU-only
check.

## Deprecated `np.int` errors

The original gradient metric helper uses `np.int`, which can fail on newer
NumPy releases. Patch a local evaluation copy to use the built-in `int` or a
specific NumPy integer type if you need to run the original scripts on modern
NumPy. Record this as an environment compatibility patch.

## Excel workbook cannot be written

The full LR/HR evaluators write an `.xlsx` file inside `pred-dir`. Ensure the
prediction directory is writable and that no existing workbook is open in
another program.

## Synthetic compositing creates unexpected files or symlinks

Some static-background scripts symlink repeated background frames. Video
variants read background videos and can be slow or fail on codec dependencies.
Run compositing only in a scratch output directory with enough space, and do not
reuse it as a default verification step.

## Speed benchmark does not match README

The README speed table is tensor throughput under specific GPU, dtype,
resolution, and downsample settings. End-to-end conversion includes media IO and
will usually be slower. Report both model-only and conversion timings separately
when diagnosing performance.
