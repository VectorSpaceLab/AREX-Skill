# Video failure modes

## Purpose

Read this when a video job stalls, resumes unexpectedly, or fails while extracting or encoding.

## Failure table

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Frame extraction fails immediately | `ffmpeg.exe` is missing, wrong, or cannot run | Restore the binary and rerun the layout check |
| The job appears to restart instead of resuming | The target folder does not yet contain enough model-specific upscaled frames | Check the frame cache and the output suffix contract |
| Encoding fails after the frames are ready | The chosen codec is unsupported or missing on the host | Let the built-in fallback retry `libx264`, or choose a safer codec |
| The frame folder stays behind after completion | Keep-frames is enabled | This is expected; turn keep-frames off if you want cleanup |
| The output lacks copied metadata | `exiftool.exe` is missing or its call fails | Restore the metadata tool if metadata matters |
| The job stops and does not continue | The stop event was set or the user requested cancel | Clear the stop condition and start a fresh job if needed |
| The output path is not what you expected | The video output path uses the same suffix contract as the frame cache | Preview the derived output paths before starting the job |

## Recovery order

1. Check the `ffmpeg.exe` asset.
2. Check the model and provider readiness.
3. Check codec fallback and the selected extension.
4. Only then debug stop/resume logic.
