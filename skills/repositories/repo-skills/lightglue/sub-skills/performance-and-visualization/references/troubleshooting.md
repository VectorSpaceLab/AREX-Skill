# Troubleshooting

## CUDA is not visible

**Symptom:** `--device cuda` fails or the benchmark falls back to CPU.

**Likely cause:** the installed PyTorch build is CPU-only, the NVIDIA driver is
missing, or CUDA is not available on this machine.

**Fix:**

- Confirm that `torch.cuda.is_available()` is `True` before asking for CUDA.
- Use `--device auto` if you just want a runnable benchmark.
- Reinstall a CUDA-enabled PyTorch build if you need GPU numbers.

## CPU-only PyTorch build

**Symptom:** the script runs, but `flash` and `compile` do not speed it up.

**Likely cause:** CPU builds do not expose the CUDA acceleration paths.

**Fix:**

- Benchmark with `--device cpu` and treat the numbers as CPU baselines.
- Focus on pruning-threshold tuning and keypoint-count sweeps instead of flash
  or compile comparisons.
- Use `--no-show` and `--save` for headless smoke tests.

## Missing flash-attn or flash path

**Symptom:** LightGlue prints a warning about FlashAttention not being available.

**Likely cause:** `flash-attn` is not installed, or the installed PyTorch build
only exposes a slower attention path.

**Fix:**

- The benchmark still works; the matcher falls back automatically.
- Use `--no-flash` if you want a clean eager baseline.
- Use the accelerated path only when comparing the same backend and build.

## `torch.compile` restrictions

**Symptom:** compiled runs are slower, fail on the selected device, or seem to
turn pruning off for small inputs.

**Likely cause:** the compile path is mainly useful on CUDA and can add overhead
for small keypoint counts.

**Fix:**

- Prefer `--compile` on CUDA only.
- Compare compiled and eager runs on the same images and keypoint counts.
- Do not expect compile to help on tiny inputs or CPU-only sessions.

## Point-pruning overhead

**Symptom:** adaptive runs are slower than the full matcher, especially on CPU
or at small keypoint counts.

**Likely cause:** pruning itself costs work, so the adaptive path is not always
worth it.

**Fix:**

- Sweep a few keypoint counts and compare `full` versus `adaptive`.
- Override pruning thresholds with `--pruning-thresholds` when you need to
  study the hardware trade-off.
- For CPU-only experiments, start with pruning disabled or delayed and then
  tighten the threshold.

## Matplotlib backend or display issues

**Symptom:** the figure window fails to open, or `plt.show()` blocks a server
job.

**Likely cause:** you are running headless or without a usable GUI backend.

**Fix:**

- Use `--no-show` and `--save out.png`.
- In your own script, switch to a non-interactive backend before importing
  `matplotlib.pyplot`.
- Call `save_plot` to produce cropped PNG or PDF files without a display.

## SuperGlue comparison needs hloc

**Symptom:** a SuperGlue comparison baseline fails with an import error.

**Likely cause:** the optional `hloc` dependency is missing.

**Fix:**

- Skip SuperGlue for LightGlue-only benchmarking.
- Install `hloc` if you specifically want the optional comparison baseline.

## First-use weight download fails

**Symptom:** extractor or matcher construction raises a download or cache error.

**Likely cause:** the pretrained weights are fetched on first use, and the
machine cannot reach the network or the cache is unavailable.

**Fix:**

- Retry after restoring network access.
- Pre-populate the model cache if the environment must run offline.
- Treat the failure as an environment problem, not a benchmark bug.
