# Root pipeline summary

For detailed pipeline operations, read `../sub-skills/pipelines/`.

PaddleX 3.7.2 includes ready-made pipeline configs for CV, OCR/document parsing, information extraction, document translation, PaddleOCR-VL, retrieval/face, time series, speech, video, and 3D tasks.

Most common entry points:

```python
from paddlex import create_pipeline
pipeline = create_pipeline("OCR", device="cpu")
```

```bash
paddlex --get_pipeline_config OCR
paddlex --pipeline OCR --input demo.png --save_path output --device cpu
```

Use a pipeline when the user wants fast inference or a pre-built end-to-end workflow. Use `../sub-skills/modules/` when the user wants dataset checking, training, evaluation, or export of individual models. Use `../sub-skills/deployment/` when the user wants HPI, serving, Paddle2ONNX, or GenAI server/client setup.
