# Extraction Troubleshooting

## Empty SRT

1. Confirm the video opens and reports nonzero frame count/FPS.
2. Confirm the subtitle area intersects visible subtitle text.
3. If Fast/Auto used VideoSubFinder, check whether it produced candidate frames
   or SRT timestamps.
4. Lower overly strict `dropScore` or area-deviation settings only after
   confirming OCR is detecting text.
5. Verify language/model selection in `ocr-backends`; English mode strips CJK
   text during extraction.

## Missed subtitles

- Increase frame extraction frequency for FPS sampling routes.
- Try Auto, then Accurate only if Fast/Auto miss many intervals.
- For multi-line or moving subtitles, expand the subtitle area and tolerance.
- Preserve empty timestamps if VideoSubFinder timing is useful but OCR text is
  intermittently missing.

## Interactive prompts block automation

Provide a subtitle area. When `sub_area` is absent, VSE may ask about watermark
or scene-text filtering after OCR. For automation, generate a plan with
`scripts/vse_cli_plan.py` and require the user to confirm coordinates first.

## Slow runs

- Full OCR is expensive; sample a short clip or use Fast mode first.
- GPU acceleration requires verified Paddle/ONNX backend availability; visible
  hardware alone is not enough.
- Reduce worker/core settings if VideoSubFinder or OCR saturates the host.

## Paths fail unexpectedly

Use ASCII-only paths without spaces for the source checkout, input video, and
output directory when debugging unexplained failures.
