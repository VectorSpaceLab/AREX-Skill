---
name: paddleocr
description: "Routes PaddleOCR users to local OCR, structured document parsing,
  hosted API, and training/deployment workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# PaddleOCR

PaddleOCR is a self-contained router for the repo's public local OCR, document parsing, hosted API, and maintenance workflows. Use this skill instead of reopening the source checkout for common user tasks.

## Start here

- Need plain OCR, text detection/recognition, orientation, unwarping, or a single model predictor? Read [`sub-skills/local-ocr-pipelines/SKILL.md`](sub-skills/local-ocr-pipelines/SKILL.md).
- Need PP-StructureV3, PaddleOCR-VL, PP-ChatOCRv4, PP-DocTranslation, or Office `doc2md` conversion? Read [`sub-skills/document-parsing-and-conversion/SKILL.md`](sub-skills/document-parsing-and-conversion/SKILL.md).
- Need hosted API calls, API auth, MCP, or LangChain integration? Read [`sub-skills/cloud-api-and-integrations/SKILL.md`](sub-skills/cloud-api-and-integrations/SKILL.md).
- Need training/config/export/deployment or TIPC evidence? Read [`sub-skills/training-export-and-deployment/SKILL.md`](sub-skills/training-export-and-deployment/SKILL.md).

## Install and smoke checks

- Base install: `python -m pip install paddleocr`
- Document parsing: `python -m pip install "paddleocr[doc-parser]"`
- Office conversion: `python -m pip install "paddleocr[doc2md]"`
- Hosted API and integrations: use the package and sibling integration docs in the cloud/integrations sub-skill.
- If HuggingFace model downloads are blocked, set `PADDLE_PDX_MODEL_SOURCE=BOS`.

Run the bundled smoke helper after installation:

```bash
python scripts/inspect_paddleocr_env.py --cli
```

At minimum, this skill expects:

```bash
python -c "import paddleocr; print(paddleocr.__version__)"
paddleocr --help
paddleocr --version
paddleocr doc2md --formats
```

## Shared references

- [`references/public-api-summary.md`](references/public-api-summary.md) for top-level exports, CLI entry points, and option objects.
- [`references/installation-and-backends.md`](references/installation-and-backends.md) for extras, Python support, backend notes, and environment variables.
- [`references/troubleshooting.md`](references/troubleshooting.md) for install/import, model download, auth, and output issues.
- [`references/repo-provenance.md`](references/repo-provenance.md) for source snapshot and staleness checks.

## Route boundaries

- Do not treat this root as a detailed manual. Pick the narrowest sub-skill that matches the task.
- Do not ask future agents to execute original repo scripts from the checkout. Use the bundled scripts or the sub-skill references instead.
- Do not rely on local GPU claims unless the task explicitly requires an accelerated backend and the relevant backend plan has been verified.

## Refresh note

If the source repository changes, compare the new checkout against `references/repo-provenance.md` and refresh the sub-skill whose evidence has drifted.
