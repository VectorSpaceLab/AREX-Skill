# Image failure modes

## Purpose

Read this when the image pipeline misbehaves after the runtime is ready.

## Failure table

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| The image job cannot start because the model path is missing | The expected `_fp16.onnx` file is absent from `AI-onnx/` | Restore the exact model filename and retry |
| The image output is not as expected for grayscale input | The grayscale path is promoted for inference and then converted back | Verify the output on a small fixture and inspect the grayscale branch before assuming a data error |
| Alpha images lose transparency or look odd | RGBA handling depends on the separate alpha pass and channel recombination | Test with a tiny RGBA fixture and confirm the selected model file exists |
| The image appears cropped at an edge after tiling | Tile combination uses integer division and can drop a remainder strip | Resize before tiling or test with a more divisible fixture |
| The output image is saved but metadata is missing | `exiftool.exe` is absent or exits with an error that the helper suppresses | Restore `exiftool.exe` if metadata retention matters |
| The output filename is unexpected | The suffix contract depends on model, resize, blending, and output path mode | Use the path helper script to preview the filename before running the GUI |
| The image job fails before any output is written | The provider or runtime package is not ready | Return to `setup-runtime` and fix the backend before debugging image logic |

## Recovery priority

1. Fix runtime/provider issues first.
2. Check the model file and asset layout.
3. Only then debug tile or channel behavior.
