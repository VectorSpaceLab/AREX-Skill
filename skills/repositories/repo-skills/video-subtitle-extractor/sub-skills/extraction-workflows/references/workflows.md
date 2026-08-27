# VSE Extraction Workflows

## Inputs

A normal hard-subtitle extraction needs:

- A readable video file. VSE uses OpenCV for frame metadata and frame reads.
- Subtitle language code such as `ch`, `en`, `japan`, `korean`, `ar`, `ru`,
  `es`, `de`, or another supported code from the OCR backend reference.
- Recognition mode: `fast`, `auto`, or `accurate`.
- Subtitle area. The source CLI accepts pixel coordinates in `ymin ymax xmin xmax`
  order; the GUI stores normalized `ymin,ymax,xmin,xmax` values and converts
  them to video pixels.
- Optional output TXT flag, word segmentation flag, save directory, confidence
  threshold, and debug-cache/debug-loss flags.

## Source CLI flow

The interactive CLI entry point prompts for video path and subtitle area:

```bash
python -m backend.main
```

It constructs `SubtitleExtractor(video_path)`, assigns `sub_area`, and calls
`run()`. The run sequence is:

1. Read video metadata: frame count, FPS, width, height.
2. Capture a frame with the selected subtitle area drawn for review.
3. Start an OCR worker process and queues.
4. Extract candidate frames by VideoSubFinder, PaddleOCR detection, or FPS
   sampling depending on mode/backend/area.
5. OCR candidate frames.
6. Optionally filter watermark or scene text when no explicit area was chosen.
7. Generate an SRT file, optionally post-process text and generate TXT.
8. Delete temporary caches unless debug cache retention is enabled.

## Non-interactive planning

The source CLI is interactive, so automation should plan first instead of
blindly piping prompts. Use:

```bash
python sub-skills/extraction-workflows/scripts/vse_cli_plan.py \
  --video movie.mp4 --area 842 1068 96 1824 --language en --mode fast \
  --output movie.srt --generate-txt
```

The helper prints the intended VSE settings, the interactive values a human
would enter, and risk checks. It does not run OCR or mutate files.

## Mode choice

| Mode | Detection route | Typical use | Risk |
| --- | --- | --- | --- |
| `fast` | VideoSubFinder + lightweight/mobile models when applicable | First attempt for most videos | May miss some lines or contain more OCR typos |
| `auto` | VideoSubFinder; model choice depends on CPU/GPU | Recommended balance | On CPU tends toward lighter models; on GPU may use server models |
| `accurate` | VSE frame-by-frame detection when CUDA is available; otherwise expensive fallback paths | Last resort for missed subtitle intervals | Very slow, especially without GPU |

## Outputs and caches

- Default SRT output is `<video stem>.srt` next to the input video unless the GUI
  save directory changes it.
- TXT output is optional and contains subtitle text lines.
- Temporary extraction data is created under VSE's output/cache area and is
  normally deleted. Enable debug cache retention only when diagnosing failures.
- Debug OCR-loss images can be emitted for selected CJK languages when enabled.

## Final verification candidates

Safe verification usually uses parser/import checks, bundled helper `--help`,
model-config probes, and tiny post-processing fixtures. Full video extraction
against sample videos is useful but can be slow and should be run only with a
short timeout and explicit backend expectations.
