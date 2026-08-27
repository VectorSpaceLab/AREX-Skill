---
name: presidio
description: "Use Presidio for PII and PHI detection, anonymization, structured
  de-identification, image/DICOM redaction, and CLI scans."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# presidio

Use this repo skill when a task needs Microsoft/Data Privacy Stack Presidio package guidance for detecting, anonymizing, pseudonymizing, redacting, or scanning personally identifiable information (PII) or protected health information (PHI).

## Start with the task shape

| User need | Read |
| --- | --- |
| Detect PII/PHI in text, configure recognizers, choose NLP engines, handle supported entities/languages, thresholds, context, or allow lists | `sub-skills/analyze-text/SKILL.md` |
| Replace, redact, hash, mask, encrypt/decrypt, custom-transform, batch anonymize, or reason about overlapping text spans | `sub-skills/anonymize-text/SKILL.md` |
| De-identify Pandas DataFrames, CSV-like columns, dictionaries, or JSON-like payloads | `sub-skills/structured-data/SKILL.md` |
| Redact standard images or DICOM burnt-in pixel text using OCR and bounding boxes | `sub-skills/image-redaction/SKILL.md` |
| Scan files, directories, or stdin from a terminal/CI job with the `presidio` CLI | `sub-skills/cli-scans/SKILL.md` |
| Install packages, pick extras, verify imports/model/OCR prerequisites | `references/install-and-models.md` and `scripts/check_presidio_install.py` |
| Run or call analyzer/anonymizer/image REST services | `references/service-and-rest-api.md` |
| Diagnose cross-cutting import/model/Tesseract/optional-extra/service issues | `references/troubleshooting.md` |
| Check whether this skill matches the current repository version | `references/repo-provenance.md` |

## Minimal Python package setup

```bash
# Text analysis plus anonymization
python -m pip install presidio-analyzer presidio-anonymizer
python -m spacy download en_core_web_lg

# Or install the convenience package for analyzer + anonymizer
python -m pip install presidio
python -m spacy download en_core_web_lg
```

Additional task-specific packages:

```bash
python -m pip install presidio-structured       # DataFrame / JSON workflows
python -m pip install presidio-image-redactor   # image and DICOM pixel redaction
python -m pip install presidio-cli              # terminal file scans
```

For image workflows, also install the Tesseract OCR system binary unless you inject another OCR engine. For optional integrations such as Transformers, Stanza, GLiNER, LangExtract, Azure AI Language, AHDS, or service mode, install only the extra needed for the selected workflow.

## Minimal verification

After installing, run the bundled checker from this skill directory:

```bash
python scripts/check_presidio_install.py --help
python scripts/check_presidio_install.py
python scripts/check_presidio_install.py --smoke
```

If the task intentionally uses only no-download pattern recognizers, the default spaCy model can be skipped:

```bash
python scripts/check_presidio_install.py --skip-model-check --skip-tesseract-check
```

Sub-skills also provide focused smoke scripts for their workflows.

## Common route combinations

- **Analyze then anonymize text:** use `analyze-text` to produce `RecognizerResult` spans, then `anonymize-text` to choose `OperatorConfig` mappings.
- **Structured de-identification:** use `structured-data`; route back to `analyze-text` only when builder entity detection or custom analyzer setup needs adjustment.
- **Image redaction:** use `image-redaction`; route to `analyze-text` for custom recognizers or analyzer kwargs and to root troubleshooting for Tesseract/model issues.
- **CI PII scan:** use `cli-scans`; route to `analyze-text` when the config needs a custom entity or model behavior beyond CLI YAML.
- **REST services:** use `service-and-rest-api` for endpoints, but use package sub-skills when custom Python objects or lambdas are required.

## Hard boundaries and cautions

- Presidio is automated detection. It can miss sensitive data; use sampling, human review, custom recognizers, and domain-specific validation for high-risk workflows.
- DICOM image redaction only edits pixel data. It does not scrub metadata PHI.
- Keep analyzer span offsets aligned with the exact text passed to anonymizer.
- Do not install all extras by default; cloud/LLM/model/GPU integrations add credentials, downloads, services, or backend constraints.
- This generated skill is self-contained. Do not rely on the original repository checkout for runtime instructions.
