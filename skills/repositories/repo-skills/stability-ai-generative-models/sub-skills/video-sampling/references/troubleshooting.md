# Video Sampling Troubleshooting

## Missing or Inaccessible Checkpoints

**Symptoms**
- `FileNotFoundError` for `checkpoints/*.safetensors`.
- Hugging Face download fails with authorization, gated repo, or license error.
- SV4D2 fails immediately with an assertion on `model_path`.

**Causes**
- Required checkpoint was not downloaded into `checkpoints/`.
- Hugging Face terms were not accepted or the CLI is not authenticated.
- `simple_video_sample_4d2.py` checks the basename, not only the contents, of `model_path`.

**Recovery**
- Verify the exact filenames from `references/model-and-inputs.md`.
- Accept model terms on Hugging Face, authenticate if needed, then download to `checkpoints/`.
- For SV4D2, use `checkpoints/sv4d2.safetensors` or `checkpoints/sv4d2_8views.safetensors`; do not pass renamed checkpoint files.

## CPU-Only or CUDA Failures

**Symptoms**
- `Torch not compiled with CUDA enabled`, `CUDA error`, or `AssertionError` from device handling.
- Full sampling is extremely slow or appears hung on CPU.

**Causes**
- Scripts default to `device='cuda'` and instantiate large video diffusion models.
- Some helper paths allocate tensors directly on CUDA.

**Recovery**
- Treat full sampling as GPU-bound. Use `Fire --help` or `scripts/inspect_video_sampling_cli.py` for CPU-safe planning.
- If debugging with `--device cpu`, expect impractical runtime and possible code-path assumptions that still require CUDA.
- Install a PyTorch build compatible with the machine CUDA runtime before attempting real sampling.

## Out of Memory

**Symptoms**
- CUDA OOM during VAE decode, video encoder conditioning, or sampler execution.
- Process is killed without a Python traceback.

**Causes**
- `decoding_t` controls how many frames are decoded at a time and is often the largest VRAM spike.
- `encoding_t` controls video encoder batching for SV4D/SV4D2.
- `img_size=576`, high frame/view counts, and long chunks increase memory.

**Recovery**
- SVD/SV3D: lower `--decoding_t` from 14 to 8, 4, 2, or 1.
- SV4D/SV4D2: lower both `--encoding_t 1` and `--decoding_t 1`.
- SV4D/SV4D2: lower `--img_size 512` if batching reductions are not enough.
- Reduce `--num_steps` to shorten runtime; this is more of a speed/quality knob than a memory fix.

## Invalid Image Input for SVD or SV3D

**Symptoms**
- `ValueError: Path is not valid image file.`
- `ValueError: Folder does not contain any images.`
- No files are processed from a folder.

**Causes**
- `simple_video_sample.py` accepts only a single `.jpg/.jpeg/.png` file or a directory of those images.
- It does not support glob patterns.
- File suffixes are checked literally for files and case-insensitively for directory entries.

**Recovery**
- Pass a single supported image or a folder containing supported images.
- For glob/pattern input, use SV4D/SV4D2 video scripts only, or expand the glob in shell and call image sampling per file.
- Check that the folder is not empty and filenames end in `.jpg`, `.jpeg`, or `.png`.

## Invalid Video, Folder, or Glob Input for SV4D/SV4D2

**Symptoms**
- `ValueError: Path is not a valid video file.`
- `ValueError` with no message for a path that is neither file, folder, nor glob.
- `Input video contains N frames, fewer than 21 frames.`
- Folder/pattern appears to load 0 frames.

**Causes**
- Video files must be `.gif` or `.mp4`.
- Folder/glob inputs must resolve to `.jpg/.jpeg/.png` frame files.
- SV4D preprocessing requires exactly 21 frames; SV4D2 requires exactly `n_frames`, default 21.
- Glob patterns are recognized only when the `input_path` string contains `*`.

**Recovery**
- Use a valid `.gif`/`.mp4`, a frame folder, or a quoted glob like `--input_path 'frames/*.png'`.
- Ensure the glob is quoted so the script sees the `*` and can sort/slice frames itself.
- Provide the required frame count for preprocessing: SV4D must read 21 frames, and SV4D2 must read exactly `--n_frames` frames after slicing, default 21.
- Zero-pad frame names so lexicographic sorting matches time order.

## Wrong Camera List Lengths

**Symptoms**
- Assertion says to provide 1 value or a list of 21 values for `elevations_deg`.
- Assertion says to provide a list of 21, 5, or 9 values for `azimuths_deg`.
- SV4D2 list assertions fail when switching from 4-view to 8-view checkpoint.

**Causes**
- SV3D_p and SV4D reference generation always require 21 camera values when lists are supplied.
- SV4D2 4-view mode needs total-view lists of 5 values including the input view.
- SV4D2 8-view mode needs total-view lists of 9 values including the input view.

**Recovery**
- For SV3D_p/SV4D, pass one scalar elevation or exactly 21 elevations, and omit azimuths or pass exactly 21 values.
- For SV4D2 `sv4d2.safetensors`, pass one scalar elevation or exactly 5 elevations, and omit azimuths or pass exactly 5 values.
- For SV4D2 `sv4d2_8views.safetensors`, pass one scalar elevation or exactly 9 elevations, and omit azimuths or pass exactly 9 values.
- Quote Fire list arguments, for example `--elevations_deg '[0,0,0,0,0]'`.

## Background Removal and Cropping Problems

**Symptoms**
- `ModuleNotFoundError` or runtime failure involving `rembg` or `onnxruntime`.
- Foreground object is cropped too tightly, too small, or disappears.
- Transparent RGBA inputs behave differently from RGB images.

**Causes**
- SV3D applies `rembg` automatically for non-RGBA input images.
- SV4D/SV4D2 use `rembg` only when `--remove_bg True`; otherwise they infer object bounds from non-white pixels.
- `image_frame_ratio` changes the crop/pad scale before resizing.

**Recovery**
- Install `rembg` and its runtime dependencies if using SV3D RGB inputs or `--remove_bg True`.
- Prefer pre-segmented RGBA images or videos when automatic removal is unstable.
- Tune `--image_frame_ratio`: decrease it to leave more border around the object, or increase it to make the object fill more of the frame.
- For real-world noisy backgrounds, segment foreground externally before running SV4D/SV4D2.

## Resolution and Quality Warnings

**Symptoms**
- Warning that image dimensions are not divisible by 64.
- Warning that SVD conditioning frame is not `576x1024`.
- Warning that SV3D conditioning frame is not `576x576`.
- Output quality is poor after unusual resizing.

**Causes**
- Video diffusion models were trained at specific resolutions.
- The SVD script attempts to round dimensions down to multiples of 64.
- SV3D/SV4D/SV4D2 assume square object-centric framing.

**Recovery**
- Prepare SVD/SVD-XT images at `576x1024`.
- Prepare SV3D/SV4D/SV4D2 images or video frames at `576x576` or let preprocessing resize after a clean crop.
- Use `--img_size 512` only as a low-VRAM compromise for SV4D/SV4D2.

## FPS and Motion Bucket Warnings

**Symptoms**
- Warning for high `motion_bucket_id`.
- Warning for small or large `fps_id`.

**Causes**
- `motion_bucket_id > 255` is flagged as potentially suboptimal.
- `fps_id < 5` or `fps_id > 30` is flagged as potentially suboptimal.

**Recovery**
- Start from defaults: `--fps_id 6 --motion_bucket_id 127`.
- Change these only when intentionally exploring motion amount or playback conditioning.
- If artifacts appear after changing them, return to defaults before debugging checkpoints or preprocessing.

## Video Write or ffmpeg Issues

**Symptoms**
- `imageio` errors while writing `.mp4`.
- Output folders exist but videos are missing or corrupt.
- `.gif` writing works but `.mp4` fails.

**Causes**
- `imageio.mimwrite` needs an available video writer backend, commonly ffmpeg.
- Output path may not be writable or disk may be full.

**Recovery**
- Install/enable an ffmpeg backend for the Python environment.
- Confirm the output folder is writable and has free space.
- Try writing `.gif` only for helper paths that support it; the standalone sampling scripts normally write `.mp4` outputs.

## SV4D Depends on SV3D References

**Symptoms**
- SV4D fails before loading the SV4D model or before dense sampling.
- Error mentions `sv3d_u`, `sv3d_p`, camera lists, or first-frame reference views.

**Causes**
- Original SV4D samples reference multi-views from the first video frame using SV3D.
- Missing SV3D checkpoints or invalid SV3D camera parameters block the whole SV4D workflow.

**Recovery**
- Ensure `checkpoints/sv3d_u.safetensors` is present for default SV4D.
- If using `--sv3d_version sv3d_p`, ensure `checkpoints/sv3d_p.safetensors` and valid 21-value camera lists or scalar elevation.
- Validate first-frame preprocessing with a clean, centered, white-background or RGBA object.

## SV4D2 Basename and View-Mode Mismatch

**Symptoms**
- Assertion failure immediately after startup.
- 8-view request produces only 4 view videos, or camera list length assertions mention 5 instead of 9 values.

**Causes**
- SV4D2 mode is selected exclusively by `os.path.basename(model_path)`.
- `sv4d2.safetensors` selects 4 generated views; `sv4d2_8views.safetensors` selects 8 generated views.

**Recovery**
- Use `--model_path checkpoints/sv4d2_8views.safetensors` for 8-view mode.
- Keep the checkpoint basename exact, even if the file is symlinked from another location.
- Match `elevations_deg` and `azimuths_deg` list lengths to the selected mode: 5 total views for `sv4d2`, 9 total views for `sv4d2_8views`.
