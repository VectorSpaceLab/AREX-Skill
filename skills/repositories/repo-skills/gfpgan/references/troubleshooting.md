# GFPGAN Troubleshooting

## Purpose

Read this when GFPGAN import, checkpoint loading, device selection, OpenCV image handling, or optional dependency setup fails.

## Common Failures

### 1. `ModuleNotFoundError` for `basicsr`, `facexlib`, `torch`, or `cv2`

**Likely causes**
- The runtime environment is missing the package set required by GFPGAN.
- The user installed only `gfpgan` without its runtime dependencies.

**What to do**
- Reinstall the package stack listed in `references/installation.md`.
- Run `python scripts/check_env.py` to confirm imports and signatures.

### 2. `GFPGANer` cannot find a checkpoint

**Likely causes**
- `model_path` points to a missing file.
- The caller assumed automatic downloads when the helper was configured not to download.
- The selected version (`1`, `1.2`, `1.3`, `1.4`, `RestoreFormer`) does not match the local filename.

**What to do**
- Confirm the checkpoint filename in `references/installation.md`.
- Point the helper or CLI at a local file explicitly.
- If the user wants network downloads, make that an explicit choice rather than the default.

### 3. OpenCV or JPEG degradation errors during dataset prep

**Symptoms**
- `cv2.imencode` argument/type errors
- Strange degradation failures when loading FFHQ training data

**Likely causes**
- OpenCV and NumPy versions are incompatible with the BasicSR degradation path.
- The environment has a newer OpenCV wheel than the repo evidence expects.

**What to do**
- Use the package versions validated for the inspection environment.
- If a helper script is involved, reduce it to a tiny disk fixture and validate the failure on the smallest reproducible input.

### 4. `lmdb` import or runtime problems

**Symptoms**
- LMDB import errors
- Dataset code fails on `.lmdb` layouts

**Likely causes**
- The environment has an incompatible `lmdb` wheel for the Python runtime.
- The data path does not end in `.lmdb` when the config declares the LMDB backend.

**What to do**
- Prefer the pinned `lmdb` version from the installed inspection environment.
- Ensure `dataroot_gt` and `io_backend.type` agree.

### 5. CUDA is unavailable

**Symptoms**
- `torch.cuda.is_available()` is false
- GPU-only smoke checks or training cannot run

**Likely causes**
- CPU-only PyTorch wheel
- No visible CUDA device
- Missing driver/runtime compatibility

**What to do**
- Use the CPU-safe inference path if the task only needs clean inference and a local checkpoint.
- For training or GPU-native validation, move to a CUDA-capable environment.
- Do not treat a CPU import as proof of GPU readiness.

### 6. Face helper loads but inference returns poor or no face results

**Likely causes**
- The input is not a face image or crop.
- `has_aligned` is wrong for the input.
- The detector misses the face or the crop is too small.

**What to do**
- Use the aligned-crop path only for already aligned face crops.
- Increase input quality or use a more centered face crop.
- Check the output folder for cropped/restored face artifacts as well as the pasted-back image.

### 7. Background upsampler confusion

**Symptoms**
- The user expects Real-ESRGAN background enhancement, but the output is face-only.
- Background enhancement errors on CPU.

**Likely causes**
- `bg_upsampler=None` or `--no-bg-upsampler` was selected.
- Real-ESRGAN was not installed.
- The user requested the old default path on CPU.

**What to do**
- Decide explicitly whether background enhancement is needed.
- Install `realesrgan` only when the user wants background upsampling.

### 8. Training config or checkpoint mismatch

**Symptoms**
- `GFPGANModel` build fails
- Losses or networks are missing
- Resume or pretrain loading errors

**Likely causes**
- The YAML config does not match the expected network/loss keys.
- Pretrained paths are absent or point to incompatible checkpoints.
- Component crops were enabled without a landmark file.

**What to do**
- Start from one of the bundled training configs and adjust only the required paths and optional flags.
- Verify `network_g`, `network_d`, and `train` sections together.
- If `crop_components: true`, provide the landmark pth file and confirm its keys match the training data names.

## When to Stop

Stop and ask the user when:
- They want to install a missing host-level dependency or a GPU stack change could affect the machine.
- They need optional Real-ESRGAN, but the current environment cannot satisfy it.
- They need full training or large-data verification instead of a smoke check.
