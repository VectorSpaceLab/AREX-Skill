---
name: ocr-service
description: "Operate Sparrow OCR FastAPI service for file and URL OCR,
  first-page PDF conversion, bounding boxes, table fallback, and response
  diagnostics."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# OCR Service

Use this sub-skill when a task involves Sparrow OCR service operation or diagnostics: uploaded image/PDF OCR, remote image/PDF URL OCR, `/api/v1/sparrow-ocr` endpoint shape, Paddle-style OCR response post-processing, optional bounding boxes, debug output, and experimental table-enhancement fallback.

Do not use this sub-skill for downstream Vision/LLM document extraction; route those tasks to [document-extraction](../document-extraction/SKILL.md). Do not use it for the Sparrow LLM API or CLI surfaces; route those tasks to [api-engine-and-cli](../api-engine-and-cli/SKILL.md).

## Read first

- [OCR API reference](references/ocr-api.md) for endpoints, request fields, content types, PDF handling, and response shape.
- [Troubleshooting](references/troubleshooting.md) for upload versus URL failures, poppler/PaddleOCR issues, bbox shape surprises, table fallback, and debug side effects.
- [OCR response smoke script](scripts/ocr_response_smoke.py) to verify bbox extraction from a fixture Paddle-style JSON without loading PaddleOCR models.

## Safe operating sequence

1. Confirm the running service base URL and port. The API paths are stable, but examples and deployments may choose different ports.
2. Use `/api/v1/sparrow-ocr/docs` or `/api/v1/sparrow-ocr/openapi.json` to confirm the live route schema before sending production traffic.
3. For a quick non-model check, call `/api/v1/sparrow-ocr/features` or run `python scripts/ocr_response_smoke.py --dump-json` from this sub-skill directory.
4. For inference, submit exactly one primary input: multipart `file` or form `image_url`. If both are present, the upload path takes precedence.
5. Treat full `/inference` requests as model execution: the first call can initialize PaddleOCR and download model assets.

## Boundaries and guarantees

This sub-skill is self-contained runtime guidance distilled from Sparrow OCR behavior. It intentionally does not require the original source checkout. Full PaddleOCR model execution is optional and was not required for this sub-skill draft; use the bundled smoke script for response-shape validation that must avoid OCR weight downloads.
