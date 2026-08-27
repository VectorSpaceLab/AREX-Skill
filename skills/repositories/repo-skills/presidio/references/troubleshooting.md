# Presidio Troubleshooting

Use this root reference for cross-cutting install, model, OCR, optional dependency, and service failures. For workflow-specific fixes, follow the nearest sub-skill troubleshooting reference.

## Quick triage

```bash
python scripts/check_presidio_install.py
python scripts/check_presidio_install.py --smoke
```

If the task is intentionally pattern-only and does not use image OCR:

```bash
python scripts/check_presidio_install.py --skip-model-check --skip-tesseract-check
```

## Import or package not found

Symptoms:

- `ModuleNotFoundError: No module named 'presidio_analyzer'`
- `ModuleNotFoundError: No module named 'presidio_anonymizer'`
- CLI command `presidio` is not found

Likely causes and fixes:

1. Install the workflow-specific distribution from `references/install-and-models.md`.
2. Confirm the import name differs from the distribution name for hyphenated packages, for example `presidio-image-redactor` imports as `presidio_image_redactor`.
3. For CLI tasks, install `presidio-cli` and verify `presidio --help`.
4. Avoid mixing package installs across multiple active Python environments.

## Default spaCy model missing

Symptoms:

- Presidio Analyzer fails while constructing `AnalyzerEngine()`.
- Error mentions `en_core_web_lg`, `Can't find model`, or a missing spaCy model.

Fixes:

```bash
python -m spacy download en_core_web_lg
python scripts/check_presidio_install.py --smoke
```

If the task only needs regex or deny-list recognizers, use `NoOpNlpEngine` and custom recognizers instead of the default analyzer path. See `sub-skills/analyze-text/SKILL.md` and `sub-skills/analyze-text/scripts/custom_recognizer_smoke.py`.

## Tesseract missing for image redaction

Symptoms:

- `pytesseract.pytesseract.TesseractNotFoundError`
- Image redaction imports work, but OCR returns no text or fails immediately.

Fixes:

1. Install the Tesseract OCR system binary for the operating system.
2. Make sure `tesseract` is on `PATH`, or configure `pytesseract.pytesseract.tesseract_cmd` in the application.
3. Run `python sub-skills/image-redaction/scripts/image_ocr_smoke.py --import-only`, then run the full smoke without `--import-only`.
4. If OCR runs but finds no words, adjust image resolution, contrast, orientation, `ocr_kwargs`, and Tesseract language data before tuning analyzer entities.

## Optional integration import errors

Symptoms:

- Import errors for `transformers`, `stanza`, `gliner`, `langextract`, Azure SDK packages, or AHDS classes.
- Runtime errors asking for an endpoint, credential, model id, or local service.

Fixes:

1. Confirm the integration is actually required for the task. Base Presidio workflows do not need all extras.
2. Install only the relevant extra from `references/install-and-models.md`.
3. For cloud integrations, provide credentials and endpoints at runtime; do not store them in skill files or prompts.
4. For model integrations, pre-download or cache the model when the environment cannot fetch models during execution.
5. For GPU acceleration, verify the underlying framework device before assuming Presidio uses the GPU.

## REST service problems

Symptoms:

- `/health` endpoint does not respond.
- Service returns 400/422/500 JSON errors.
- Docker container starts but analyzer requests fail with model errors.

Fixes:

1. Confirm the right service is running: analyzer, anonymizer, or image redactor.
2. Check ports and endpoints in `references/service-and-rest-api.md`.
3. For analyzer/image services, confirm the NLP model and Tesseract prerequisites are installed inside the service environment or image.
4. Analyzer service config files are controlled by environment variables such as `ANALYZER_CONF_FILE`, `NLP_CONF_FILE`, and `RECOGNIZER_REGISTRY_CONF_FILE`.
5. Anonymizer REST rejects custom lambda operators for safety; use package APIs for custom in-process operators.

## Data privacy and validation cautions

- Presidio is automated PII detection; it can miss sensitive data. Use review, sampling, and domain-specific recognizers for high-risk workflows.
- DICOM image redaction only edits pixel data. It does not scrub metadata PHI.
- Keep analyzer results aligned with the exact input text passed to anonymizer; stale spans cause invalid span errors.
- Validate outputs on tiny representative fixtures before batch processing sensitive data.
