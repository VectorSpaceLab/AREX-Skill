---
name: pipelines
description: "Use PaddleX pre-trained pipelines through create_pipeline, the
  paddlex pipeline CLI, config export, prediction, result saving, devices,
  engines, and parallel inference."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# PaddleX pipelines

Use this sub-skill when the user wants to run or configure a **pre-trained PaddleX pipeline**: image/CV pipelines, OCR/document pipelines, time-series pipelines, speech/video pipelines, retrieval/face pipelines, 3D pipelines, or VLM/document-understanding pipelines.

Route away from this sub-skill when the task is:

- single-model custom development, dataset checking, training, evaluation, export, or `create_model` usage — use `../modules/`.
- serving, high-performance inference deployment, Paddle2ONNX, GenAI server/client setup, or plugin installation — use `../deployment/`.

## Start here

1. Identify whether the user already has a built-in pipeline name or a local pipeline YAML.
2. For Python API usage, use `from paddlex import create_pipeline`.
3. For CLI usage, use `paddlex --pipeline ...` or `paddlex --get_pipeline_config ...`.
4. Decide device and engine separately from the pipeline name. CPU is the safest baseline; GPU/HPI and GenAI-backed routes require matching install extras or plugins.
5. For multi-artifact document pipelines, save to a directory instead of forcing a single output file.

Read `references/pipeline-catalog.md` for supported family names, common workflow patterns, and output behavior. Read `references/pipeline-troubleshooting.md` when pipeline creation, input parsing, result saving, backend selection, or remote service setup fails.

## Minimal Python pattern

```python
from paddlex import create_pipeline

pipeline = create_pipeline(
    pipeline="image_classification",  # or a local YAML path / config dict
    device="cpu",
)
for result in pipeline.predict("demo.jpg"):
    result.print()
    result.save_to_json("output")
    result.save_to_img("output")
```

Verified installed signature for PaddleX 3.7.2:

```text
create_pipeline(pipeline=None, *, config=None, device=None, engine=None,
                engine_config=None, pp_option=None, use_hpip=None,
                hpi_config=None, **kwargs) -> BasePipeline
```

Important precedence rule: explicit Python/CLI arguments such as `device`, `engine`, `use_hpip`, `engine_config`, or pipeline-specific keyword arguments override defaults from a named pipeline or exported YAML config.

## Minimal CLI patterns

```bash
# Export a built-in pipeline config before editing it.
paddlex --get_pipeline_config image_classification

# Run prediction from the CLI.
paddlex --pipeline image_classification --input demo.jpg --save_path output --device cpu

# Use a local YAML config.
paddlex --pipeline ./pipeline.yaml --input demo.jpg --save_path output
```

## Bundled helper

Use `scripts/run_pipeline_smoke.py` when you need a small reusable wrapper that checks importability, creates a pipeline, runs `predict`, and tries common save methods without depending on the original PaddleX checkout.

Examples:

```bash
python scripts/run_pipeline_smoke.py --dry-run
python scripts/run_pipeline_smoke.py --pipeline image_classification --input demo.jpg --save-path output --device cpu
python scripts/run_pipeline_smoke.py --pipeline OCR --input demo.png --save-path output/ocr --kwargs-json '{"use_doc_orientation_classify": false}'
```

The helper may trigger model downloads when you create a real pipeline. Use `--dry-run` for a no-download install/API check.

## High-value checks before answering a user

- Is the pipeline name exact? Names are case-sensitive in several document pipelines (`OCR`, `PP-StructureV3`, `PaddleOCR-VL`).
- Is the input type supported by that pipeline? Document pipelines may accept images, PDFs, URLs, or directories; time-series pipelines usually expect CSV/tabular inputs.
- Does the task require remote LLM/GenAI credentials or a running server (`PP-DocTranslation`, `PP-ChatOCRv4`, PaddleOCR-VL variants)? If yes, route deployment details to `../deployment/`.
- Does the user ask for high-performance inference, serving, or Paddle2ONNX? Use `../deployment/` even if the source object is a pipeline.
