# Runtime troubleshooting

## Purpose

Read this when install or launch problems remain after the basic dependency and asset checklist.

## Failure table

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Module import fails on Python 3.11 or older | The source uses Python 3.12-compatible syntax | Use Python 3.12+ for inspection and runtime work |
| Import fails on Linux with Windows subprocess names missing | The app is Windows-oriented | Treat this as a platform limit for the app runtime, not a generic install problem |
| `onnxruntime` imports but the provider list does not include DirectML | The wrong runtime wheel is installed or the host cannot expose the backend | Install the intended DirectML runtime on Windows and re-check the provider list |
| The GUI starts but no model can be loaded | Model files are missing from `AI-onnx/` or have the wrong names | Restore the exact `_fp16.onnx` files |
| `ffmpeg.exe` or `exiftool.exe` is missing | The required asset folder is incomplete | Restore the binary and rerun the layout check |
| The app crashes at startup after preferences load | The versioned JSON is malformed | Remove or repair the preferences file under the user's Documents folder |

## Recovery order

1. Fix Python version or platform mismatch first.
2. Fix the provider and asset layout next.
3. Only then move into image or video workflow troubleshooting.

## When to stop

Stop and request the correct Windows runtime when the required backend is not available. Do not claim successful app readiness from a CPU-only or Linux-only inspection result.
