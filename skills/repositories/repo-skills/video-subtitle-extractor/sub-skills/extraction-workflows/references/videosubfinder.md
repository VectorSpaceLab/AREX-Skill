# VideoSubFinder Integration

VSE bundles platform-specific VideoSubFinder binaries and calls them during
Fast/Auto extraction when an explicit subtitle area exists and Accurate GPU
frame-by-frame detection is not selected.

## Platform choices

- Windows: `VideoSubFinderWXW.exe` with bundled DLLs and optional CUDA flag.
- Linux: `VideoSubFinderCli.run`.
- macOS: `VideoSubFinderCli`.

The generated skill does not copy those large binaries. It documents how VSE
uses them so agents can troubleshoot a VSE checkout or release.

## Area conversion

VSE converts pixel subtitle coordinates to VideoSubFinder crop fractions:

- `top_end = 1 - ymin / frame_height`
- `bottom_end = 1 - ymax / frame_height`
- `left_end = xmin / frame_width`
- `right_end = xmax / frame_width`

A wrong area can cause VideoSubFinder to emit no candidate images or to focus on
watermarks/scene text.

## CPU threads and decoder

The source sets CPU thread counts from available CPUs minus a reserve, unless
`videoSubFinderCpuCores` is configured. The decoder option is `OpenCV` by
default; switch to `FFmpeg` when OpenCV video decoding fails, while watching for
minor timeline shifts.

## Troubleshooting signs

- No `Frame:` progress or no RGB candidate images: binary failed, wrong input
  path, unsupported codec, wrong decoder, or invalid crop area.
- Candidate frames exist but final SRT is empty: OCR dropped all boxes, wrong
  language/model, low confidence, or subtitle area too strict.
- Process hangs: terminate the child process group and retry with a simple path,
  reduced thread count, or a different decoder.
