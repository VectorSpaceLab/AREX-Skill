---
name: ocr
description: "Routes LayoutParser OCR wrappers, response parsing, and text
  aggregation workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# OCR

Use this sub-skill when the task is about extracting text from images or
parsing saved OCR responses into LayoutParser objects.

## What belongs here

- `TesseractAgent` and `TesseractFeatureType`
- `GCVAgent` and `GCVFeatureType`
- OCR response loading, saving, and aggregation
- live OCR setup, credentials, and language selection

## What does not belong here

- Layout detection model inference: use `layout-models`
- Geometry or reading-order logic after OCR: use `layout-objects`
- Box/text rendering: use `visualization`
- PDF or JSON/CSV loading: use `layout-io`

## Read these files

- `references/guide.md` for agent behavior, aggregation levels, and troubleshooting notes
- `../layout-objects/SKILL.md` when you need to group or sort OCR blocks
- `../visualization/SKILL.md` when you need to render OCR output

## Fast path

1. Decide whether the task needs live OCR or only saved-response parsing.
2. Use Tesseract for local OCR and GCV for Google Cloud Vision workflows.
3. Confirm the backend package and host dependency before constructing the
   agent.
4. Aggregate at the required level before post-processing the OCR output.
5. Keep saved responses when you need deterministic follow-up tests.

## Common user requests

- "Use Tesseract OCR on this image"
- "Parse a saved Google Vision response"
- "Group the OCR output by line"
- "Load OCR results back into LayoutParser"
- "Set the custom Tesseract binary path"

## Minimal smoke

The environment inspector confirms the optional OCR backends and the local
`tesseract` binary:

```bash
python ../../scripts/inspect_backends.py
```

## Failure clues

- `pkg_resources` missing after installing GCV usually means the setuptools
  build is not compatible with `google-cloud-vision==1`.
- Missing `tesseract` binary means the Python wrapper is present but live OCR
  cannot run.
- Missing credentials mean the GCV live API path is not ready.
- If the output text changes across runs, use a saved response instead of live
  OCR for tests.

## Output discipline

When answering, name the OCR engine, the language or credential assumption,
and the desired aggregation level. If the task only needs saved-response
parsing, say so explicitly so future agents do not over-install the runtime.
