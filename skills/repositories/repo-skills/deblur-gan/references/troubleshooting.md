# DeblurGAN troubleshooting

## Cross-cutting issues

### CUDA training is required for the perceptual-loss path

**Symptom**: the model crashes when it reaches the content-loss or gradient-penalty code.

**Likely cause**: the selected training path is trying to use GPU-only tensor moves or VGG19 feature extraction on a CPU-only build.

**Fix**:
- Install a CUDA-enabled PyTorch build.
- Verify `torch.cuda.is_available()` before launching training.
- Use the CPU path only for inference or data-preparation work.

### The source training script hardcodes a local dataroot and option overrides

**Symptom**: the run ignores the data path or configuration you passed.

**Likely cause**: the shipped `train.py` overwrites parsed options with local values.

**Fix**:
- Use the bundled training wrapper.
- Pass your desired `--dataroot`, `--gan_type`, `--resize_or_crop`, and `--fineSize` explicitly.
- Do not copy the source script's hardcoded path into a reusable command.

### The source inference script imports `ssim` directly

**Symptom**: `test.py` fails immediately on import.

**Likely cause**: the external `ssim` package is missing.

**Fix**:
- Use the bundled inference wrapper, which relies on the local `util.metrics.SSIM` helper instead.
- If you need strict source-script parity, install the extra package separately.

### `Visualizer` fails before any images are saved

**Symptom**: training or inference errors while opening the log file.

**Likely cause**: `checkpoints_dir/name` does not exist yet.

**Fix**:
- Create the directory before constructing the visualizer.
- The generated wrappers do this automatically.

### Live plotting is unavailable

**Symptom**: the run fails or warns about visdom.

**Likely cause**: display mode is active but `visdom` is not installed.

**Fix**:
- Use the wrappers' headless mode.
- Install `visdom` only if you want interactive browser plots.

### The `unaligned` loader path is not reliable

**Symptom**: the repository mentions `unaligned`, but the workflow breaks when you try to use it.

**Likely cause**: the factory does not initialize that loader correctly in this checkout.

**Fix**:
- Treat it as unsupported routing.
- Use `aligned` for paired data or `single` for inference input.

### VGG19 weights are missing or blocked

**Symptom**: the perceptual-loss path stalls or errors while fetching pretrained features.

**Likely cause**: the machine is offline or model downloads are blocked.

**Fix**:
- Allow the download once if the machine can reach the model host.
- If the machine must stay offline, pre-stage the weights in the environment cache.

### OpenCV is missing for pair creation

**Symptom**: the pair helper fails on `import cv2`.

**Likely cause**: the environment lacks the OpenCV wheel.

**Fix**:
- Install `opencv-python-headless`.
- Re-run the helper after the import succeeds.

## Where to look next

- For folder and filename issues, read the data-preparation sub-skill.
- For checkpoint and result-tree questions, read the inference sub-skill.
- For training schedule or optimizer issues, read the training sub-skill.
- For a quick import and CUDA sanity check, run `scripts/check_deblurgan_env.py`.
