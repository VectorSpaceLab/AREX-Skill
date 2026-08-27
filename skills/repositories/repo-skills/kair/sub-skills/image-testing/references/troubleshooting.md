# KAIR image-testing troubleshooting

Use this reference when a KAIR image inference/evaluation workflow cannot find weights or images, produces unexpected metrics, runs out of memory, or fails around GPEN/custom ops.

## Missing checkpoint or unexpected download

Symptoms:

- `FileNotFoundError` around `model_zoo/*.pth` or `model_zoo/swinir/*.pth`.
- `main_test_swinir.py` prints that it is downloading a model.
- A download stalls or creates a tiny invalid checkpoint file.

Facts and fixes:

- Most classic image checkpoints live directly under `model_zoo/`.
- SwinIR checkpoints live under `model_zoo/swinir/`.
- VRT/RVRT checkpoints live under video-specific folders and are owned by `../video-restoration/SKILL.md`.
- The original SwinIR test script downloads missing model files from its release URL. Prefer an explicit dry-run/download plan when network use must be controlled.
- Use the root model-zoo/download reference to map group names to filenames before downloading.
- If a downloaded checkpoint is suspiciously small, delete it only after confirming it is not a real local model, then re-download explicitly.

## No images found or OpenCV reads `None`

Symptoms:

- The script asserts no image paths exist.
- Results folder is empty.
- OpenCV raises errors because an image is `None`.

Checks:

1. Confirm the dataset root is correct and contains real image files, not an extra nested folder.
2. For DnCNN-style scripts, `--testsets testsets --testset_name set12` resolves to `testsets/set12`.
3. For SwinIR paired SR, `--folder_gt` should point at the HR folder and `--folder_lq` at a matching LR folder.
4. For SwinIR denoising/JPEG CAR, the script reads clean GT images from `--folder_gt` and generates degradations internally.
5. For real-world SR, use `--folder_lq`; no GT metrics are computed.
6. Verify images with the data-preparation checker:

   ```bash
   python sub-skills/data-preparation/scripts/check_dataset_layout.py image --root testsets/set12
   ```

## Wrong noise, channel count, or checkpoint family

Symptoms:

- Shape mismatch loading checkpoint weights.
- Denoising output is poor despite no runtime error.
- A color image is processed as grayscale or vice versa.

Fixes:

- DnCNN checkpoint names control channel count: names containing `color` use 3 channels; most others use grayscale.
- Match `--noise_level_img` or `--noise` to the checkpoint sigma when using fixed-noise models: common values are 15, 25, and 50.
- FDnCNN/FFDNet hard-coded scripts use noise-level maps; patch both image and model sigma constants deliberately.
- SwinIR denoising uses different checkpoint families for `gray_dn` and `color_dn`.
- SwinIR JPEG CAR uses `--jpeg` values 10, 20, 30, or 40 and window size 7.

## Scale, folder, or filename mismatch in SR

Symptoms:

- SR script cannot locate LR files.
- Metrics are unexpectedly missing or low.
- Output size does not align with GT.

Fixes:

- Match SR checkpoint scale and command scale (`x2`, `x3`, `x4`, `x8`).
- For SwinIR classical/lightweight SR, LQ filenames commonly use suffixes such as `babyx4.png`, while GT uses `baby.png`.
- For hard-coded SR scripts that generate LR from HR, `L_path == H_path` means benchmark degradation is generated internally; this is not the same as testing arbitrary LR inputs.
- For USRNet, ensure `kernels/kernels_12.mat` or the selected kernel file exists and the scale loop matches the checkpoint (`usrgan` variants are usually x4-focused).

## SwinIR out of memory

Symptoms:

- CUDA OOM during SwinIR inference.
- Large images fail while small images pass.

Fixes:

- Add `--tile <size>` and keep it compatible with the task window size:
  - window 8 for most SwinIR tasks;
  - window 7 for JPEG CAR.
- Increase or decrease `--tile_overlap` to trade seam quality against memory.
- For real-world SR, start with `--tile 400` and adjust downward if needed.
- If CPU is selected, expect much slower inference; tile can still reduce RAM.

## `ModuleNotFoundError: op` in face enhancement

Symptoms:

- `main_test_face_enhancement.py` fails importing `op`, `FusedLeakyReLU`, or `upfirdn2d`.
- Custom CUDA extension build errors appear before any face is processed.

Facts:

- KAIR's face-enhancer network imports `op` as a top-level module even though the source lives under the checkout's `models/op` directory.
- A working run needs the KAIR `models/` directory on the Python import path or an equivalent local wrapper that adds it deliberately.
- The `op` modules JIT-build CUDA extensions and need PyTorch, `ninja`, CUDA-capable hardware/runtime, and compatible compiler/toolkit.

Fixes:

1. Verify `RetinaFace-R50.pth` and `GPEN-BFR-512.pth` are under `model_zoo/`.
2. Run from a KAIR checkout and ensure Python can import both `retinaface` and the `models/op` package.
3. If a wrapper is needed, add the checkout's `models` directory to `PYTHONPATH` only for this command, and document that local choice.
4. If the extension build fails, clear the relevant PyTorch extension cache only after preserving the error log, then retry with a compatible CUDA toolkit and `TORCH_CUDA_ARCH_LIST` for the user's GPU.

## RetinaFace or GPEN weight mismatch

Symptoms:

- Face detection finds no faces.
- `load_state_dict` reports missing or unexpected keys.
- Output faces are blank or heavily distorted.

Fixes:

- Match the script's expected model names: `RetinaFace-R50.pth` and `GPEN-BFR-512.pth` for the updated path; older comments mention `GPEN-512.pth`.
- Confirm `need_face_detection` matches the input: use detection for uncropped photos; disable only when images are already aligned face crops.
- Lowering the detection threshold is a local script change; record it and avoid treating it as a model-quality issue until the weights and image scale are correct.

## Challenge profiling failures

`main_challenge_sr.py` is not a general inference script. It is reference-only for FLOPs, activation count, parameter count, runtime, and max-memory reporting.

Common issues:

- It is hard-coded for specific model names and folders.
- Runtime and memory timing use CUDA events and require a CUDA device.
- `print_modelsummary` should be false for runtime/max-memory measurement and true for FLOPs/activations.
- Missing `model_zoo/msrresnet_x4_psnr.pth` or `model_zoo/imdn_x4.pth` fails before profiling.

## Download/network side effects

Before allowing a script to auto-download:

1. Confirm the user wants network access.
2. Confirm destination directories such as `model_zoo/swinir` or `model_zoo/`.
3. Prefer single model names or a selected group instead of `all` when disk/network budget matters.
4. Preserve partially downloaded files only when they are large and resumable; otherwise remove corrupted tiny files after inspection.

## Safe preflight commands

These are cheap parser checks, not evidence that a model or dataset is ready:

```bash
python main_test_dncnn.py --help
python main_test_swinir.py --help
python main_download_pretrained_models.py --help
python sub-skills/image-testing/scripts/build_image_test_command.py --help
```

Full inference should be treated as a native test only after the generated skill is integrated and the required local checkpoint/data are available.
