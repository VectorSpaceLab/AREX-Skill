# Local OCR Workflows

This reference covers the common `PaddleOCR` pipeline and the most common ways to route through the local OCR surface.

## When to use the pipeline

Use `PaddleOCR` when you want a complete OCR pass over an image, scan, or PDF page and you want text boxes plus recognized text in one call. Use a standalone predictor only when the task is about a single model family such as text detection or text recognition.

## Python workflow

```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(
    lang="en",
    ocr_version="PP-OCRv6",
)
results = ocr.predict("image.jpg")

for res in results:
    res.print()
    res.save_to_img("./output/")
    res.save_to_json("./output/result.json")
```

Common call pattern:

- `predict(input, **params)` returns a list.
- `predict_iter(input, **params)` streams results lazily.
- `close()` releases the predictor.

## CLI workflow

The package CLI exposes a local OCR route for the same pipeline family. Use `paddleocr --help` to see the exact installed subcommand list, then run the OCR subcommand with an input image or PDF and the model options you need.

General advice:

- Use the CLI when you want to confirm argument names or debug a single command line.
- Use the Python API when you need to inspect result objects, customize post-processing, or integrate with another application.

## Model selection

The local OCR workflow uses language and OCR-version routing to choose detector and recognizer names.

Typical defaults:

- `PP-OCRv6` is the default OCR family.
- Earlier families such as `PP-OCRv5`, `PP-OCRv4`, and `PP-OCRv3` remain available for compatibility and language-specific fallbacks.
- `lang` values such as `ch`, `en`, `fr`, `ru`, `ar`, `hi`, `japan`, and related variants are mapped by the wrapper.

If a language/version combination is unsupported, the wrapper raises a clear error instead of silently choosing a different model family.

## Result handling

OCR results usually include:

- detection polygons
- recognition text
- confidence scores
- optional visualized or saved artifacts

Use the result object's `print()`, `save_to_img()`, and `save_to_json()` helpers instead of manually reconstructing output paths.

## Relationship to the single-model predictors

The same package also exposes model-level predictors for text detection, text recognition, image orientation, unwarping, layout detection, table detection, and other model families. Use this workflow for the end-to-end OCR route; use the model reference for a single predictor class.
