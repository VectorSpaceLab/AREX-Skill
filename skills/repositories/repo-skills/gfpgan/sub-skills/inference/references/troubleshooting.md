# GFPGAN Inference Troubleshooting

## Missing Checkpoint

**Symptoms**
- `FileNotFoundError` for a `.pth` file.
- Helper exits with a message naming the expected version file.

**Recovery**
- Pass `--model-path` to an existing local checkpoint.
- Check the version map in `references/model-selection.md`.
- Use `--allow-download` only after the user agrees to network/cache writes.

## Wrong Version or Architecture

**Symptoms**
- State-dict load errors.
- Unexpected strict-load failures.

**Recovery**
- Pair the checkpoint with the correct `--version`.
- `1` maps to `arch='original'` and `channel_multiplier=1`.
- `1.2`, `1.3`, and `1.4` map to `arch='clean'` and `channel_multiplier=2`.
- `RestoreFormer` maps to `arch='RestoreFormer'`.

## No Face Detected or Empty Outputs

**Likely causes**
- The input is too small, blurry, profile-only, or not a face.
- `--aligned` was used on a whole image.
- `--only-center-face` skipped off-center faces.

**Recovery**
- Remove `--aligned` for whole images.
- Remove `--only-center-face` for group photos.
- Crop or upscale very small faces before restoration.
- Inspect saved cropped faces to confirm detection.

## CPU/GPU Behavior

**Symptoms**
- Very slow full-image restoration.
- Optional background upsampler fails or is disabled.

**Recovery**
- Run without background upsampler for CPU usage.
- Verify `torch.cuda.is_available()` when the task requires GPU.
- Do not claim GPU readiness from a CPU-only import check.

## Optional Real-ESRGAN Missing

**Symptoms**
- `ModuleNotFoundError: realesrgan`.
- Background enhancement is unavailable while face restoration still works.

**Recovery**
- Switch to `--no-bg-upsampler` for face-only restoration.
- Install `realesrgan` only when the user actually needs background enhancement.

## OpenCV Image Read Failures

**Symptoms**
- `cv2.imread` returns `None`.
- The helper reports an unreadable input.

**Recovery**
- Confirm the path exists and is a supported image file.
- Convert unusual image formats to PNG/JPEG first.
- For RGBA inputs, prefer `--ext png` for output.

## Output Extension or Suffix Surprise

**Symptoms**
- Output images have unexpected extensions or filenames.

**Recovery**
- Use `--ext auto` to preserve the input extension.
- Use `--ext png` to force PNG output.
- Use `--suffix name` only when the user wants suffix-tagged restored faces/images.

## Runtime OOM

**Symptoms**
- CUDA out-of-memory during face restoration or background upsampling.

**Recovery**
- Disable background upsampling first.
- Reduce upscaling or tile background upsampling when Real-ESRGAN is used.
- Process fewer images per run; the bundled helper processes images sequentially.
