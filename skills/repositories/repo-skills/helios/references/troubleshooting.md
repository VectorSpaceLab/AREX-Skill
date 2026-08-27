# Cross-cutting troubleshooting

## 1. Helios imports fail early

**Symptoms**
- Import errors from `helios.modules.helios_kernels`
- Flash-attention or kernel variant lookup failures
- `No module named 'kernels'` or a build-variant mismatch

**Likely causes**
- The environment is missing the `kernels` package.
- The selected torch/CUDA wheel does not have a matching Helios kernel build.
- The environment is too new or too old for the available kernel variants.

**Recovery**
- Run `scripts/check_helios_env.py`.
- Reconcile the torch/CUDA wheel with a `kernels` variant that supports it.
- Keep the generation workflow on CUDA; do not treat a CPU-only import as
  proof that the generation backend is ready.

## 2. Demo import is slow or hangs

**Symptoms**
- Importing the demo module downloads weights or starts compiling immediately.
- Startup appears to block before any UI appears.

**Likely causes**
- The demo preloads and AOTI-compiles model components at import time.
- The GPU, network, or model cache is not ready yet.

**Recovery**
- Treat the demo as a deployment-style workflow, not a quick import smoke test.
- Use the distilled checkpoint and a warm CUDA environment.

## 3. Video export fails

**Symptoms**
- The inference helper cannot write an mp4 file.
- Export raises an imageio/ffmpeg-related error.

**Likely causes**
- `imageio-ffmpeg` is missing or the ffmpeg plugin cannot be resolved.
- The output path is unwritable.

**Recovery**
- Re-run `scripts/check_helios_env.py` and confirm `imageio-ffmpeg` is installed.
- Make sure the output directory exists and is writable.

## 4. GPU backend is missing

**Symptoms**
- `torch.cuda.is_available()` is false.
- Inference or training scripts fail before model construction.

**Recovery**
- Switch to a CUDA-capable environment.
- If you only need metadata or config validation, use the data-preparation or
  training validation helpers instead of trying to run generation.

## 4. Unsupported package combinations

**Symptoms**
- `xformers`, `DeepSpeed`, or NPU-specific imports are missing.
- A launcher script assumes a capability that is not installed.

**Recovery**
- Treat these as optional extras unless the specific route explicitly requires
  them.
- Prefer the baseline CUDA path first, then add optional accelerators one at a
  time.
