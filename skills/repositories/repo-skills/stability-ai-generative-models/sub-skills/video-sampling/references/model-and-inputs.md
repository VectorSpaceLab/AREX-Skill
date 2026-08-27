# Models, Checkpoints, and Inputs

## Checkpoint Map

Place checkpoints under `checkpoints/` with the expected filenames. The sampling scripts and config files refer to these names directly.

| Workflow | Config | Required checkpoint(s) | Hugging Face source named in docs |
| --- | --- | --- | --- |
| SVD | `svd.yaml` | `checkpoints/svd.safetensors` | `stabilityai/stable-video-diffusion-img2vid` |
| SVD-XT | `svd_xt.yaml` | `checkpoints/svd_xt.safetensors` | `stabilityai/stable-video-diffusion-img2vid-xt` |
| SVD image decoder | `svd_image_decoder.yaml` | `checkpoints/svd_image_decoder.safetensors` | SVD image-decoder release/checkpoint variant |
| SVD-XT image decoder | `svd_xt_image_decoder.yaml` | `checkpoints/svd_xt_image_decoder.safetensors` | SVD-XT image-decoder release/checkpoint variant |
| SV3D_u | `sv3d_u.yaml` | `checkpoints/sv3d_u.safetensors` | `stabilityai/sv3d` |
| SV3D_p | `sv3d_p.yaml` | `checkpoints/sv3d_p.safetensors` | `stabilityai/sv3d` |
| SV4D | `sv4d.yaml` | `checkpoints/sv4d.safetensors` plus `sv3d_u.safetensors` or `sv3d_p.safetensors` | `stabilityai/sv4d` and `stabilityai/sv3d` |
| SV4D2 | `sv4d2.yaml` | `checkpoints/sv4d2.safetensors` | `stabilityai/sv4d2.0` |
| SV4D2 8-view | `sv4d2_8views.yaml` | `checkpoints/sv4d2_8views.safetensors` | `stabilityai/sv4d2.0` |

Checkpoint downloads may require accepting Hugging Face model terms and using authenticated `huggingface-cli download ... --local-dir checkpoints` commands. Do not rename SV4D2 checkpoint files: `simple_video_sample_4d2.py` asserts the `model_path` basename is exactly `sv4d2.safetensors` or `sv4d2_8views.safetensors`.

## Version and Model Selection

- Use `simple_video_sample.py --version svd` for 14-frame image-to-video at `576x1024`.
- Use `simple_video_sample.py --version svd_xt` for 25-frame image-to-video at `576x1024`.
- Use `simple_video_sample.py --version sv3d_u` for 21-frame image-to-multi-view orbit at `576x576` without explicit camera conditioning.
- Use `simple_video_sample.py --version sv3d_p` for 21-frame image-to-multi-view orbit with explicit elevation/azimuth conditioning.
- Use `simple_video_sample_4d.py --sv3d_version sv3d_u|sv3d_p` for original SV4D; it first creates SV3D reference views from the first frame.
- Use `simple_video_sample_4d2.py --model_path checkpoints/sv4d2.safetensors` for SV4D2 4 generated views per chunk.
- Use `simple_video_sample_4d2.py --model_path checkpoints/sv4d2_8views.safetensors` for SV4D2 8 generated views per chunk.

## Input Formats

| Script | Accepted input forms | Supported extensions | Notes |
| --- | --- | --- | --- |
| `simple_video_sample.py` | Single image file or directory | `.jpg`, `.jpeg`, `.png` | Directory entries are sorted and each image is sampled independently. Glob patterns are not supported. |
| `simple_video_sample_4d.py` | Single video file, image directory, or image glob | `.gif`, `.mp4`, `.jpg`, `.jpeg`, `.png` | Preprocessing requires exactly 21 frames after reading/slicing. |
| `simple_video_sample_4d2.py` | Single video file, image directory, or image glob | `.gif`, `.mp4`, `.jpg`, `.jpeg`, `.png` | Defaults to `n_frames=21`; preprocessing requires exactly `n_frames` frames. |

For folders and globs, files are sorted lexicographically. Name frame files with zero padding (`frame_0001.png`, `frame_0002.png`) to preserve temporal order.

## Frame and View Counts

| Workflow | Conditioning input | Generated length/shape | Camera/list requirements |
| --- | --- | --- | --- |
| SVD | One image at a time | 14 frames | No camera list. |
| SVD-XT | One image at a time | 25 frames | No camera list. |
| SV3D_u | One image at a time | 21 frames/views | No explicit camera list. |
| SV3D_p | One image at a time | 21 frames/views | `elevations_deg` scalar or 21 values; `azimuths_deg` omitted or exactly 21 values. |
| SV4D | 21 input video frames | 21 frames x 8 novel views, plus diagonal | SV3D reference orbit uses scalar or 21 elevations and omitted or 21 azimuths. |
| SV4D2 | Default 21 input video frames | 12-frame x 4-view chunks autoregressed to `n_frames`; 4 generated view videos | `elevations_deg` scalar or 5 values; `azimuths_deg` omitted or 5 values. |
| SV4D2 8-view | Default 21 input video frames | 5-frame x 8-view chunks autoregressed to `n_frames`; 8 generated view videos | `elevations_deg` scalar or 9 values; `azimuths_deg` omitted or 9 values. |

## Camera Parameter Expectations

- `elevations_deg` is in degrees. For SV3D_p/SV4D reference generation, a scalar is expanded to 21 values. For SV4D2, a scalar is expanded to total views including the input view: 5 for `sv4d2.safetensors`, 9 for `sv4d2_8views.safetensors`.
- `azimuths_deg` is in degrees. When omitted, the scripts generate default orbits. When provided, use one value per generated timestep/view count required by the selected workflow.
- SV3D_p internally converts elevations to polar radians as `90 - elevation` and computes relative azimuths from the last azimuth value. Give azimuths in increasing orbit order to match the README guidance.
- SV4D2 defaults include the input view at azimuth `0`: 4-view mode uses `[0, 60, 120, 180, 240]`; 8-view mode uses `[0, 30, 75, 120, 165, 210, 255, 300, 330]`.

## Resolution and Preprocessing

- SVD/SVD-XT were trained for `576x1024`; the script warns when the conditioning frame differs and attempts to resize dimensions that are not divisible by 64.
- SV3D, SV4D, and SV4D2 target square `576x576` images or video frames.
- SV3D preprocessing removes background for non-RGBA images, crops object alpha, composites onto white, and resizes to `576x576`.
- SV4D/SV4D2 preprocessing can optionally use `--remove_bg True`; otherwise it assumes a mostly white background and crops around non-white content.
- `image_frame_ratio` controls how large the detected object is inside the square frame. The scripts compute padded side length as detected box size divided by this ratio, so lower ratios leave more border and higher ratios make the object fill more of the frame. Use it when objects are cropped too tightly or appear too small.

## Runtime Prerequisites

- Full sampling needs an installed generative-models environment with `torch`, `torchvision`, `omegaconf`, `fire`, `einops`, `imageio`, `Pillow`, `opencv-python`, and the repo package available.
- `remove_bg=True` and SV3D non-RGBA image preprocessing require `rembg` and its model/dependency stack.
- Writing `.mp4` through `imageio.mimwrite` may require a usable ffmpeg backend in the Python environment.
- CUDA is the practical target for real sampling. Help/static inspection is the safe fallback on CPU-only machines.
