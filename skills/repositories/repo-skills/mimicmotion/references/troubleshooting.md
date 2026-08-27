# Troubleshooting

## Purpose

Read this when MimicMotion fails to import, the runtime stack is incomplete, or generation stops before a video is written.

## 1) `ImportError: cannot import name 'cached_download' from 'huggingface_hub'`

**Typical symptom**

- Importing `inference.py`, `predict.py`, or `diffusers` fails immediately.

**Likely cause**

- `diffusers 0.27.0` is being used with a newer `huggingface-hub` release that no longer exports `cached_download`.

**Recovery**

- Pin `huggingface-hub==0.20.2` in the same environment as `diffusers==0.27.0`.
- Re-run `python -m pip check` and `scripts/check_runtime.py`.

## 2) `decord 0.6.0 is not supported on this platform`

**Typical symptom**

- `pip check` complains about `decord`, or the package imports inconsistently.

**Likely cause**

- The PyPI wheel does not match the host/platform combination.

**Recovery**

- Use the conda-forge `decord=0.6.0` build or another verified platform-specific build.
- Reinstall into a clean private prefix rather than trying to repair a broken environment in place.

## 3) CUDA is unavailable

**Typical symptom**

- `torch.cuda.is_available()` is false.
- The pipeline fails when it reaches CUDA-only calls.

**Likely cause**

- CPU-only torch, a missing GPU passthrough, an incompatible driver/wheel pair, or an environment that was created without a CUDA runtime.

**Recovery**

- Use the verified CUDA wheel pair and confirm `nvidia-smi` sees the GPU.
- Re-run `python -c "import torch; print(torch.cuda.is_available())"` and the bundled runtime checker.
- Do not treat a CPU import as proof of a supported runtime path.

## 4) `CUDAExecutionProvider` is missing from ONNXRuntime

**Typical symptom**

- DWPose imports, but pose inference cannot use the GPU path.

**Likely cause**

- `onnxruntime-gpu` is missing or the environment picked the CPU-only provider set.

**Recovery**

- Install `onnxruntime-gpu==1.29.0` in the same environment.
- Re-check `onnxruntime.get_available_providers()`.

## 5) `ffmpeg` / `write_video` errors

**Typical symptom**

- Video writing fails at the final save step.

**Likely cause**

- `ffmpeg` is missing from the environment or the system library stack is incomplete.

**Recovery**

- Confirm `ffmpeg -version` works.
- In containerized setups, add the system packages listed in `references/environment.md`.

## 6) Missing local weights or example assets

**Typical symptom**

- `models/DWPose/yolox_l.onnx`, `models/DWPose/dw-ll_ucoco_384.onnx`, or `models/MimicMotion_1-1.pth` cannot be found.
- The Cog predictor tries to download weights but setup never completes.

**Likely cause**

- The model directory was not populated yet, or network access is unavailable.

**Recovery**

- Verify the file layout described in `references/configuration.md`.
- Use the bundled runtime checker with `--skip-models` if you only want to confirm the Python stack.
- If you need the full workflow and network downloads are blocked, stop and resolve network access or use the required local cache.

## 7) Input validation failures

**Typical symptom**

- Errors such as `Resolution must be a multiple of 8`, `Number of frames must be greater than frames overlap`, or `FPS must be between 1 and 60`.

**Likely cause**

- The Cog predictor bounds or the sample config were violated.

**Recovery**

- Use the canonical bounds in `references/configuration.md`.
- For quick tests, start from `configs/test.yaml` and adjust one field at a time.

## 8) The pipeline seems to fall back to CPU

**Typical symptom**

- The source CLI can choose `cpu` if CUDA is absent.

**Why this is still a problem**

- The verified runtime path for this skill is CUDA-only; the CPU branch is not treated as a supported substitute.

**Recovery**

- Install or repair the CUDA-capable environment rather than trying to use the CPU branch.
- If you must draft guidance before full hardware verification, treat that as a partial limitation and do not claim the workflow is fully verified.

## Next checks to run

1. `python scripts/check_runtime.py --repo-root <checkout>`
2. `python -m pip check`
3. `ffmpeg -version`
4. `nvidia-smi`
