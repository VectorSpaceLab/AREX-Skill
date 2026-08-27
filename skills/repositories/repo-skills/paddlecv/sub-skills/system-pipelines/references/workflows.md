# Workflows

## OCR preset
```python
from paddlecv import PaddleCV

ocr = PaddleCV(task_name="PP-OCRv3")
result = ocr("paddlecv/demo/00056221.jpg")
```

## OCR + IE / SA / TTS presets
- `PP-OCRv3-IE` adds information extraction.
- `PP-OCRv3-SA` adds sentiment analysis.
- `PP-OCRv3-TTS` adds text-to-speech output.

These presets are useful when the user wants a packaged end-to-end workflow rather than separate operators.

## PP-Structure and direct system configs
```python
from paddlecv import PaddleCV

pipe = PaddleCV(config_path="paddlecv/configs/system/PP-Structure-table.yml")
result = pipe("paddlecv/demo/table.jpg")
```

Use the direct config path when the user needs:
- a table-only or layout-only variant,
- a different connector chain,
- or a graph that is not exposed as a `task_name`.

## Retrieval / recognition presets
- `PP-ShiTu` and `PP-ShiTuV2` are the packaged image retrieval / recognition workflows.
- They are the right place to start when the user wants a bundled gallery or similarity workflow rather than a single embedding model.

## Human / vehicle / pose presets
- `PP-Human` and `PP-Human-Attr` cover person analysis flows.
- `PP-Vehicle` and `PP-Vehicle-Attr` cover vehicle analysis flows.
- `PP-TinyPose` covers the packaged pose-estimation route.

## Decision rule
If the user says "I want the packaged OCR / structure / retrieval workflow", choose this sub-skill even if the underlying graph contains single-model operators and connectors.
