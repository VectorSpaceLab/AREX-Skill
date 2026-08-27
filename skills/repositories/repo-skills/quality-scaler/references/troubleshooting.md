# Cross-cutting troubleshooting

## Purpose

Read this when the problem is not specific to image or video processing yet: install/import failures, backend/provider problems, asset layout issues, and settings corruption.

## Common failures

| Symptom | Likely cause | What to do next |
| --- | --- | --- |
| `SyntaxError` while importing the source module on Python 3.11 or older | The module uses Python 3.12-era f-string syntax | Use Python 3.12 or newer for source inspection and runtime work |
| `ImportError` for `STARTUPINFO` or `STARTF_USESHOWWINDOW` | The source is Windows-specific and expects the Windows `subprocess` API | Treat this as a Windows runtime requirement; do not claim Linux support for the app itself |
| `ModuleNotFoundError` for `customtkinter`, `natsort`, `psutil`, `Pillow`, `opencv-python-headless`, or `onnxruntime` | Runtime dependencies are not installed | Install the runtime dependency set described in `shared-runtime-and-assets.md` |
| The app launches but the AI provider is unavailable | `onnxruntime` does not expose `DmlExecutionProvider` or the wheel is not the DirectML build | Install the documented DirectML wheel on Windows and confirm the provider list before launching |
| Missing model file errors or the UI cannot upscale any image/video | `AI-onnx/<model>_fp16.onnx` files are absent | Restore the model files with the exact filenames listed in `shared-runtime-and-assets.md` |
| Frame extraction or video encoding fails immediately | `Assets/ffmpeg.exe` is missing or the app cannot execute it | Restore the `ffmpeg.exe` asset and re-check the asset path |
| Metadata copy silently does nothing | `Assets/exiftool.exe` is missing or exits with an error that the helper suppresses | Treat metadata copy as best-effort; restore `exiftool.exe` if metadata retention matters |
| The app falls back to defaults or crashes when reading preferences | The JSON preference file is malformed | Delete or repair the versioned preferences JSON under the user's Documents folder and relaunch |
| Outputs look clipped or a narrow border is missing on large tiled images | Tile splitting uses integer division after a tiling threshold and can drop remainder pixels on non-divisible dimensions | Reduce tiling stress by resizing first, or inspect the generated output on a small fixture before trusting the result |
| The app reads a file that is not really supported | File selection is based on filename extension | Rename or convert the input to a supported extension before retrying |

## Decision tree

1. If the source module does not import, fix Python version and platform assumptions first.
2. If the module imports but AI inference fails, verify the DirectML provider and model assets.
3. If image or video workflows fail later, move to the image or video sub-skill troubleshooting page.

## Read next

- `../sub-skills/setup-runtime/SKILL.md` for install and launch routing.
- `../sub-skills/image-upscaling/SKILL.md` for image-specific issues.
- `../sub-skills/video-upscaling/SKILL.md` for video-specific issues.
- `../scripts/inspect_qualityscaler_layout.py` for a quick file-layout check.
