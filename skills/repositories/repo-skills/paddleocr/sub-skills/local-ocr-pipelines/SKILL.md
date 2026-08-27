---
name: local-ocr-pipelines
description: "Routes PaddleOCR users to local OCR, single-model predictors, and
  engine/device troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Local OCR and Model Pipelines

Use this route when the task is about PaddleOCR's local OCR pipeline or a standalone predictor class. If the user wants full document parsing, Office conversion, or hosted service usage, route them elsewhere.

## Handle these tasks here

- General OCR with `PaddleOCR`.
- Standalone predictors such as `TextDetection`, `TextRecognition`, `DocImgOrientationClassification`, `TextLineOrientationClassification`, `TextImageUnwarping`, `LayoutDetection`, `FormulaRecognition`, `ChartParsing`, `DocVLM`, `TableClassification`, `TableCellsDetection`, `TableStructureRecognition`, and `SealTextDetection`.
- CLI subcommands like `paddleocr ocr`, `paddleocr text_detection`, `paddleocr text_recognition`, and the other single-model predictors.
- Model-name selection, language fallback, and engine/device configuration for local inference.

## Route away from here

- `PPStructureV3`, `PaddleOCRVL`, `PPChatOCRv4Doc`, `PPDocTranslation`, and `doc2md` belong in `document-parsing-and-conversion`.
- Official hosted API, MCP, and LangChain integrations belong in `cloud-api-and-integrations`.
- Training, export, deployment, and TIPC evidence belong in `training-export-and-deployment`.

## Read these references

- [`references/ocr-workflows.md`](references/ocr-workflows.md) for end-to-end OCR recipes and language/model selection.
- [`references/model-and-engine-reference.md`](references/model-and-engine-reference.md) for model families, default subcommands, and engine flags.
- [`references/troubleshooting.md`](references/troubleshooting.md) for model download, backend, and language/version failures.

## Use the bundled script

- [`scripts/run_ocr_pipeline.py`](scripts/run_ocr_pipeline.py) wraps the public `PaddleOCR` API with safe defaults for local runs.

## What future agents should know

- `PaddleOCR` is the end-to-end OCR pipeline; it returns a list of result objects that can be printed or saved.
- The common control surface comes from the shared PaddleX wrapper: `device`, `engine`, `engine_config`, `enable_hpi`, `use_tensorrt`, `precision`, `enable_mkldnn`, `cpu_threads`, and `enable_cinn`.
- The CLI and Python APIs share the same basic model-selection logic. Default OCR is PP-OCRv6; older versions and language-specific fallbacks are documented in the workflow reference.
- For standalone predictors, prefer the model-class names and CLI subcommands over ad hoc source checkout scripts.
- Keep CPU import/help checks separate from accelerated backend claims.

## Common triggers

- "Run OCR on this image"
- "Why did PP-OCRv6 choose this model name?"
- "How do I use text detection / recognition directly?"
- "What engine should I use for this predictor?"
- "Why is the language or model combination unsupported?"
