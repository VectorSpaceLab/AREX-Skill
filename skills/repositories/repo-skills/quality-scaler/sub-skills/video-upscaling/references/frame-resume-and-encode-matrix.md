# Frame resume and encode matrix

## Purpose

Read this when you need the filename rules, resume logic, codec mapping, and fallback behavior for video jobs.

## Resume matrix

| Condition | Behavior |
| --- | --- |
| Target folder missing | Start a fresh extraction |
| Target folder exists and already has more than one upscaled frame for the selected model | Resume from the remaining original frames |
| Target folder exists but the model-specific upscaled frame count is not sufficient | Treat it as a fresh job |

## Output filename contract

Video outputs use the same suffix contract as images, but they also keep the selected video extension. The output directory and video filename both include:

- model name
- input resize percent
- output resize percent
- optional blending tag

The extracted frame names are always JPEGs.

## Codec matrix

| User selection | Effective codec |
| --- | --- |
| `x264` | `libx264` |
| `x265` | `libx265` |
| `h264_nvenc`, `hevc_nvenc`, `h264_amf`, `hevc_amf`, `h264_qsv`, `hevc_qsv` | passed through as selected |

## Encode behavior

- The app builds a concat list for the upscaled frames.
- Audio is copied from the original video when available.
- The selected codec is tried first.
- If that fails, the app retries with `libx264` as a fallback.
- After successful encode, metadata is copied from source to output.

## Keep-frames behavior

- If keep-frames is off, the frame directory is removed after successful encode.
- If keep-frames is on, the frame directory is preserved for inspection or future resume behavior.

## Practical note

A frame-based resume is only useful if the frame filenames still match the selected model and output suffixes. If you change those settings, the previous frame cache no longer counts as a valid resume target.
