# Extraction API Reference

## `SubtitleExtractor`

`SubtitleExtractor(vd_path)` is the central source class. Important runtime
attributes and methods:

| Surface | Purpose |
| --- | --- |
| `video_path`, `video_cap`, `frame_count`, `fps`, `frame_width`, `frame_height` | Video metadata and OpenCV capture state. |
| `sub_area` | Pixel subtitle area object with `ymin`, `ymax`, `xmin`, `xmax`; `None` enables broader detection and interactive filtering. |
| `subtitle_output_path` | Destination SRT path; default is beside the video. |
| `run()` | Full extraction pipeline. Starts OCR worker, extracts frames, post-processes, writes output, and cleans caches. |
| `extract_frame_by_vsf()` | Uses bundled VideoSubFinder to find subtitle frames in Fast/Auto routes. |
| `extract_frame_by_det()` | Uses PaddleOCR text detection over frames, mainly for accurate GPU-capable routes. |
| `extract_frame_by_fps()` | Samples frames by configured extraction frequency. |
| `generate_subtitle_file()` / `generate_subtitle_file_vsf()` | Writes final SRT from OCR/raw/VSF timing evidence. |
| `_remove_duplicate_subtitle()` | Groups similar consecutive OCR text using Levenshtein ratio and config threshold. |
| `srt2txt()` | Writes optional TXT output from SRT lines. |

## Configuration surfaces consumed by extraction

Extraction uses values from VSE's config object, including:

- `language`, `mode`, `generateTxt`, `wordSegmentation`
- `hardwareAcceleration`
- `extractFrequency`, `dropScore`, `thresholdTextSimilarity`
- `subtitleArea`, `subtitleAreaDeviationRate`, `subtitleAreaDeviationPixel`
- `debugOcrLoss`, `debugNoDeleteCache`, `deleteEmptyTimeStamp`
- `videoSubFinderCpuCores`, `videoSubFinderDecoder`

## Integration cautions

- The source class is not a stable installed-library API; treat it as a source
  integration surface for agents working in a VSE checkout.
- `run()` starts processes/threads and can execute platform binaries. Do not
  call it from a verifier or test prompt unless the user accepted those side effects.
- If assigning `subtitle_output_path`, choose a path before calling `run()`.
- When `sub_area is None`, the CLI may prompt for watermark/scene-text filtering;
  automation should avoid that by providing an explicit area.
