# Provider and asset validation

## Purpose

Read this when the app imports but the AI path still fails, or when you need to distinguish a missing asset problem from a missing backend problem.

## Provider expectation

- The source requests `DmlExecutionProvider` when it builds the ONNX inference session.
- The intended runtime wheel is the DirectML build on Windows.
- A CPU-only ONNX runtime may be enough for read-only inspection, but it is not the intended app runtime.

## Asset expectation

| Asset | Why it matters |
| --- | --- |
| `AI-onnx/<model>_fp16.onnx` | AI model weights for image and video upscaling |
| `Assets/ffmpeg.exe` | frame extraction and video re-encoding |
| `Assets/exiftool.exe` | metadata copy from input media to output media |
| GUI images and icon files | visual assets required by the app shell |

## Model set expectation

The app expects one file per model family:

- `LVAx2_fp16.onnx`
- `RealESR_Gx4_fp16.onnx`
- `RealESR_Ax4_fp16.onnx`
- `BSRGANx2_fp16.onnx`
- `BSRGANx4_fp16.onnx`
- `RealESRGANx4_fp16.onnx`
- `MSharpx4_fp16.onnx`
- `IRCNN_Mx1_fp16.onnx`
- `IRCNN_Lx1_fp16.onnx`

## Validation ideas

- Use the bundled layout helper to verify the asset tree.
- Check that the provider list includes the DirectML provider before you attempt GUI work on a Windows machine.
- If the provider is missing, fix the runtime before debugging image or video behavior.

## Recovery guidance

- Missing model file: restore the exact filename, not just a similarly named model.
- Missing `ffmpeg.exe`: restore the binary before trying any video job.
- Missing `exiftool.exe`: image and video output may still be created, but metadata copy cannot be trusted.
