# Shared runtime and assets

## Purpose

Read this when you need the common runtime contract for the whole QualityScaler app: platform expectations, installed dependencies, asset layout, and the files the app expects to find beside the script.

## Runtime contract

- The app is a Windows-oriented GUI for image and video upscaling.
- The source imports `onnxruntime` and requests the `DmlExecutionProvider`; the intended runtime wheel is the DirectML build on Windows.
- The source module needs Python 3.12 or newer to import cleanly because it uses 3.12-era f-string syntax.
- The GUI uses CustomTkinter and Tk widgets; launching it is not a headless workflow.
- The app stores user preferences under the user's Documents folder using a versioned filename of the form `QualityScaler_<version>_userpreference.json`.

## Public runtime dependencies

The repository documents these runtime dependencies:

- `numpy`
- `customtkinter`
- `natsort`
- `psutil`
- `Pillow`
- `opencv-python-headless`
- `onnxruntime-directml` on the intended Windows DirectML path
- `pyinstaller` as a packaging helper

## Required on-disk assets

### Model slot layout

Place the model files under `AI-onnx/` using the exact names expected by the source:

- `LVAx2_fp16.onnx`
- `RealESR_Gx4_fp16.onnx`
- `RealESR_Ax4_fp16.onnx`
- `BSRGANx2_fp16.onnx`
- `BSRGANx4_fp16.onnx`
- `RealESRGANx4_fp16.onnx`
- `MSharpx4_fp16.onnx`
- `IRCNN_Mx1_fp16.onnx`
- `IRCNN_Lx1_fp16.onnx`

### Runtime binaries and assets

Place the app assets under `Assets/` with these names at minimum:

- `ffmpeg.exe`
- `exiftool.exe`
- `logo.ico`
- `logo.png`
- `github_logo.png`
- `telegram_logo.png`
- `clear_icon.png`
- `info_icon.png`
- `stop_icon.png`
- `upscale_icon.png`

## Why these assets matter

- `ffmpeg.exe` extracts frames and re-encodes video output.
- `exiftool.exe` copies metadata from source media to output media.
- The image assets are used by the GUI and are part of the expected app layout.
- Missing models or binaries are operational errors, not optional warnings, for the intended Windows workflow.

## Read next

- `shared-settings-and-output-contract.md` for model names, formats, and output naming rules.
- `troubleshooting.md` for the common install/import and missing-asset failures.
- `../scripts/inspect_qualityscaler_layout.py` to check the expected file layout without launching the GUI.
