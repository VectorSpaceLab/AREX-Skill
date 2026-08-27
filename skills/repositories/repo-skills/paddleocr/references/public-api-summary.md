# PaddleOCR Public API Summary

This file is a compact orientation aid for future agents. Use the sub-skill references for detailed workflows and parameters.

## Top-level imports

The package exports the following common entry points from `paddleocr`:

- Local OCR and document pipelines: `PaddleOCR`, `DocPreprocessor`, `DocUnderstanding`, `FormulaRecognitionPipeline`, `PaddleOCRVL`, `PPChatOCRv4Doc`, `PPDocTranslation`, `PPStructureV3`, `SealRecognition`, `TableRecognitionPipelineV2`.
- Standalone model classes: `ChartParsing`, `DocImgOrientationClassification`, `DocVLM`, `FormulaRecognition`, `LayoutDetection`, `SealTextDetection`, `TableCellsDetection`, `TableClassification`, `TableStructureRecognition`, `TextDetection`, `TextImageUnwarping`, `TextLineOrientationClassification`, `TextRecognition`.
- Hosted API client: `PaddleOCRClient`, `AsyncPaddleOCRClient`.
- Public API types and errors: `Model`, `OCROptions`, `PPStructureV3Options`, `PaddleOCRVLOptions`, `PaddleOCRAPIError`, `AuthError`, `InvalidRequestError`, `APIError`, `JobFailedError`, `RateLimitError`, `RequestTimeoutError`, `PollTimeoutError`, `ResponseFormatError`, `ResultParseError`, `ServiceUnavailableError`, `NetworkError`.
- Office conversion helpers: `doc2md_convert`, `doc2md_supported_formats`.
- Utility export: `benchmark`, `logger`, `__version__`.

## CLI entry points

- `paddleocr` is the main package CLI.
- `paddleocr_mcp` is the MCP server entry point provided by the repository's MCP integration package.

## Common workflow families

- `PaddleOCR`: general OCR pipeline for text detection and recognition.
- `PPStructureV3` and `PaddleOCRVL`: structured document parsing and Markdown/JSON generation.
- `PaddleOCRClient` and `AsyncPaddleOCRClient`: hosted API jobs for OCR or document parsing.
- `doc2md_convert`: office document to Markdown conversion for `.docx`, `.pptx`, and `.xlsx`.

## Common option families

- OCR options: `OCROptions`.
- PP-StructureV3 options: `PPStructureV3Options`.
- PaddleOCR-VL options: `PaddleOCRVLOptions`.

## Error surface

The hosted API client raises a dedicated error hierarchy. Treat auth, request, rate-limit, timeout, service, and response-shape failures as separate troubleshooting cases rather than generic exceptions.
