# Shared settings and output contract

## Purpose

Read this when you need the common setting names, supported formats, model families, and output naming rules shared by the image and video workflows.

## Model families and scale factors

| Model | Scale |
| --- | --- |
| `LVAx2` | x2 |
| `RealESR_Gx4` | x4 |
| `RealESR_Ax4` | x4 |
| `BSRGANx2` | x2 |
| `BSRGANx4` | x4 |
| `RealESRGANx4` | x4 |
| `MSharpx4` | x4 |
| `IRCNN_Mx1` | x1 |
| `IRCNN_Lx1` | x1 |

## GUI setting families

- App zoom: `50%`, `75%`, `100%`, `125%`, `150%`, `175%`.
- AI multithreading: `OFF`, `2 threads`, `4 threads`, `6 threads`, `8 threads`.
- Blending: `OFF`, `Low`, `Medium`, `High`.
- GPU selector: `Auto`, `GPU 1`, `GPU 2`, `GPU 3`, `GPU 4`.
- Keep frames: `OFF` or `ON`.
- Image output extensions: `.png`, `.jpg`, `.bmp`, `.tiff`.
- Video output extensions: `.mp4`, `.mkv`, `.avi`, `.mov`.
- Video codecs: `x264`, `x265`, `h264_nvenc`, `hevc_nvenc`, `h264_amf`, `hevc_amf`, `h264_qsv`, `hevc_qsv`.

## Output naming contract

The app appends the same suffix pattern to image and video outputs:

- `_<AI model>`
- `_InputR-<input resize percent>`
- `_OutputR-<output resize percent>`
- `_Blending-Low|Medium|High` when blending is enabled
- the chosen extension

Examples:

- `photo_BSRGANx4_InputR-50_OutputR-100_Blending-Low.jpg`
- `clip_RealESRGANx4_InputR-50_OutputR-100_Blending-Medium.mp4`

When the output path is set to the app's coded default, the output basename is derived from the input file stem. When the user chooses a directory, the basename is preserved and the selected folder is prefixed.

## Hidden implementation contract that matters to users

- The app treats file selection as a filename-extension filter, not as a MIME probe.
- The image and video pipelines both rely on the selected model name to choose the upscale factor.
- The GUI uses the selected AI model and a VRAM limiter to compute a tile-size budget.

## Settings persistence

The GUI saves the last selected values into a JSON file under the user's Documents folder. If that file is malformed, the app can fail before the GUI reaches a usable state.

## Read next

- `../sub-skills/image-upscaling/references/image-tiling-and-format-matrix.md` for tile logic and image-format edge cases.
- `../sub-skills/video-upscaling/references/frame-resume-and-encode-matrix.md` for video suffixes, codec fallback, and frame file naming.
- `troubleshooting.md` for settings-file and output-path failures.
