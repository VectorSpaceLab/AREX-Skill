# OCR API Reference

## `OcrRecogniser`

`OcrRecogniser.predict(image)` lazily initializes a PaddleOCR 3.x recognizer and
returns sorted `(dt_box, rec_res)` values compatible with older VSE processing:

- `dt_box`: list of four-point boxes normalized to axis-aligned coordinates.
- `rec_res`: list of `(text, score)` tuples.

The recognizer chooses `device='gpu:0'` only when `HardwareAccelerator.has_cuda()`
is true; otherwise it uses CPU.

## `SubtitleDetect`

`SubtitleDetect.detect_subtitle(img)` wraps PaddleOCR `TextDetection` and
returns `dt_polys` plus an elapsed placeholder. VSE uses this for frame-by-frame
subtitle detection in accurate-style paths.

## `get_coordinates(dt_box)`

Converts four-point boxes to `(xmin, xmax, ymin, ymax)` tuples. This coordinate
order is used by subtitle-area filtering and raw subtitle lines.

## `PaddleModelConfig`

Builds model paths from the app base directory, model version `V5`, current
language, and mode. It resolves detection and recognition model directories and
optional model names from `inference.yml`.

## `HardwareAccelerator`

Singleton-like detector that checks Paddle CUDA first, then ONNX Runtime
providers. `has_accelerator()` respects the enabled flag; `has_cuda()` returns
false when hardware acceleration is disabled even if CUDA was detected.
