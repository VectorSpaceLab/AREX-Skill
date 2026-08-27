# ECCV2022-RIFE interpolation troubleshooting

Use this reference for image-pair, video-file, and numbered PNG-sequence inference failures.

## Checkpoint and model-load failures

### Symptoms

- `FileNotFoundError` or similar error for `flownet.pkl`.
- Errors after messages about trying HD model imports.
- State-dict key mismatch during `load_state_dict`.
- The user expected HD weights to work but the script says it loaded the ArXiv RIFE model.

### Causes and fixes

- The default model path is `train_log`. If weights are elsewhere, pass `--model <checkpoint-dir>`.
- For the current fallback `model.RIFE`, the checkpoint directory should contain `flownet.pkl`.
- The current source scripts try HD import paths first, but active `model.RIFE_HDv2` and `model.RIFE_HD` modules are absent in this checkout. Legacy HD files elsewhere in the source tree are not automatically used by these CLIs.
- Do not mix incompatible checkpoint families and model code. If a user supplies external HD model code inside the checkpoint tree, require them to verify the exact import path and file layout before promising support.
- Use the command builder before a run:
  ```bash
  python sub-skills/interpolation/scripts/interpolation_command_builder.py --validate image --img img0.png img1.png --model train_log
  ```

## Missing dependency or executable failures

### `ModuleNotFoundError: skvideo`, `moviepy`, `cv2`, or `torch`

Install the runtime dependency set for the source checkout: PyTorch/torchvision, NumPy, tqdm, sk-video, OpenCV, and moviepy. The repository is source-only, so installing dependencies is not the same as installing a package distribution.

### `ffmpeg` not found or video reader/writer errors

- Install `ffmpeg` and ensure it is on `PATH`.
- `skvideo.io.vreader` and the script's audio transfer path rely on ffmpeg-backed video handling.
- The Dockerfile installs ffmpeg inside the container; native host runs need their own ffmpeg installation.

### Audio transfer fails

The script first tries to copy audio losslessly, then retries AAC. If both fail, it prints an audio failure and leaves the interpolated video without audio. Audio transfer is not attempted for PNG output, PNG-directory input, or explicit `--fps` runs.

## Input image and EXR issues

### OpenCV returns `None` or tensor conversion fails

- Confirm both paths passed to `--img` exist and are readable by OpenCV.
- Confirm both images have compatible dimensions and channel counts.
- Avoid mixing EXR and non-EXR inputs. EXR mode activates only when both filenames end with `.exr`.

### Output colors look wrong

The source uses OpenCV channel conventions for image-pair mode and explicit BGR/RGB reversal in video PNG mode. If the user pre/post-processes frames with other libraries, keep channel order consistent.

### Output directory surprises

`inference_img.py` writes `output/img*.png` or `output/img*.exr` relative to the current working directory. It does not write beside the input images unless the current working directory is the input directory.

## Numbered PNG sequence issues

### `ValueError` while sorting frames

The video script expects PNG filenames whose stems are integers because it sorts with `int(name_without_extension)`. Rename frames to numeric names:

```text
0.png
1.png
2.png
...
```

Names such as `frame_000001.png`, `000001.extra.png`, or uppercase-only extensions may fail or be skipped by the simple source filter.

### Missing or unordered frames

- Check for gaps in numeric sequence before inference.
- Keep only intended PNG files in the input directory; the source includes files containing lowercase `png` in the name.
- If the directory came from ffmpeg extraction, prefer an integer naming pattern during extraction or rename before running RIFE.

## Scale, padding, and high-resolution artifacts

### Assertion failure for `--scale`

Valid video scales are exactly `0.25`, `0.5`, `1.0`, `2.0`, and `4.0`.

### 4K job is too slow or runs out of memory

- Start with `--scale 0.5` or `--UHD`.
- Reduce `--exp`; factor is `2^exp`, so `--exp 2` creates many more model calls than `--exp 1`.
- Prefer PNG output for debugging a few frames only if disk space is sufficient.
- On CPU, expect real videos to be very slow.

### Disordered or warped patterns

The README suggests trying `--scale 2.0` when videos generate disordered patterns. Also inspect for scene cuts, large motion, low-quality encodes, or mismatched frame dimensions.

### Padding-related edge cases

- Image-pair mode pads height/width to multiples of 32 and crops outputs back to the original size.
- Video mode pads to `max(32, int(32 / scale))`, then crops model outputs back to the original frame size.
- If the user modifies source scripts or post-processes tensors, preserve this pad/crop behavior.

## CPU, CUDA, and FP16 caveats

- Device choice is automatic: CUDA if PyTorch sees a GPU, CPU otherwise.
- To force CPU for a diagnostic run, hide GPUs externally, for example `CUDA_VISIBLE_DEVICES="" python inference_img.py ...`.
- CPU functional fallback exists for inference, but it is much slower and not a speed claim.
- `--fp16` changes the default tensor type to CUDA half tensors only when CUDA is available. Use it primarily on Tensor Core GPUs and disable it if output quality, unsupported-op, or dtype errors appear.
- If CUDA is expected but not used, check the PyTorch build, driver compatibility, and `torch.cuda.is_available()`.

## Video output and codec issues

- The script's OpenCV writer uses `mp4v` even if `--ext` is changed. Some extension/container combinations may be invalid or produce files that other tools dislike.
- If output video is empty or corrupt, retry with `--png` to isolate model/frame generation from video encoding.
- Then re-encode from `vid_out/%07d.png` with ffmpeg using the user's desired codec and pixel format.

## Montage and scene-cut behavior

- `--montage` crops the center half of the frame and writes side-by-side comparison frames; it is not a full-frame preservation mode.
- `--skip` is abandoned in the current script and should not be recommended as an active feature.
- The script has internal SSIM heuristics: very similar frames may be handled specially, and very dissimilar frames may be repeated to avoid bad scene-cut interpolation. If this surprises the user, explain that it is source behavior rather than a command-building error.
