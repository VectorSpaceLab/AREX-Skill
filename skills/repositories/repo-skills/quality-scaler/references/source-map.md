# QualityScaler source map

## Purpose

Use this map to locate the verified source evidence that each runtime route summarizes. The repository is a single Python entry file, so the map also clarifies which sections belong to which sub-skill.

## Source overview

| Source area | What it covers | Skill owner |
| --- | --- | --- |
| `QualityScaler.py` bootstrap and constants | app name, version, model lists, extension lists, asset paths, preference filename, GUI sizing constants | shared root references and `setup-runtime` |
| `QualityScaler.py` `AI_upscale` class | model selection, DirectML session setup, normalization, preprocessing, postprocessing, tiling, and image orchestration | `image-upscaling` |
| `QualityScaler.py` `VideoUpscaleTask` class | target naming, frame bookkeeping, resolution math, thread count selection, and resume state | `video-upscaling` |
| `QualityScaler.py` file helpers | image read/write, metadata copy, output-name builders, FPS lookup, blending, and file-type detection | shared references plus `image-upscaling` |
| `QualityScaler.py` video pipeline | frame extraction, multiprocessing upscaling, queue coordination, encoding, keep-frames cleanup, and stop/resume logic | `video-upscaling` |
| `QualityScaler.py` GUI/runtime layer | file selection, menu handlers, user preference persistence, top-level app setup, and error dialogs | `setup-runtime` and shared references |
| `README.md` | public platform claims, install steps, asset requirements, and user-facing feature list | `setup-runtime` and shared references |
| `requirements.txt` | runtime dependency list | shared runtime reference and `setup-runtime` |
| `AI-onnx/` and `Assets/` | required model slots, asset names, and runtime layout | `setup-runtime` |

## Verified public APIs and constants

- `AI_upscale(selected_AI_model, selected_gpu, input_resize_factor, tiles_resolution)`.
- `AI_upscale.AI_orchestration(image)` and the supporting normalization and tiling helpers.
- `VideoUpscaleTask(video_path, selected_output_path, selected_AI_model, selected_AI_multithreading, selected_gpu, tiles_resolution, input_resize_factor, output_resize_factor, selected_blending_factor, selected_video_extension, selected_video_codec)`.
- `upscale_image(...)` and `upscale_video(...)` as the two top-level runtime workflows.
- `prepare_output_image_filename(...)`, `resize_with_output_factor(...)`, `blend_images_and_save(...)`, `copy_file_metadata(...)`, and `get_video_fps(...)`.
- Supported image extensions: jpg, png, bmp, tif/tiff, webp, heic variants.
- Supported video extensions: mp4, webm, mkv, flv, gif, m4v, avi, mov, qt, 3gp, mpg, mpeg, vob variants.

## Owner routing notes

- `setup-runtime` should explain how the app starts, what assets must exist, what runtime dependencies are required, and what usually fails before the image or video pipeline runs.
- `image-upscaling` should explain the AI model core, tile behavior, output naming, and image-format edge cases.
- `video-upscaling` should explain frame extraction, resume logic, encoding fallback, and cleanup behavior.

## Bundle policy

The runtime skill should not depend on the original checkout being available. If a workflow needs a script, the generated skill tree must provide a bundled helper such as `../scripts/inspect_qualityscaler_layout.py`, `../scripts/launch_qualityscaler.py`, or `../scripts/derive_qualityscaler_paths.py`.
