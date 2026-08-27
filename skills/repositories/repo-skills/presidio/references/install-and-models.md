# Install and Model Reference

Read this when a task starts with installing Presidio, choosing a package, or diagnosing import/model prerequisites.

## Package map

| Workflow | Distribution(s) | Import(s) | Required non-Python prerequisite |
| --- | --- | --- | --- |
| Text PII analysis | `presidio-analyzer` / `presidio_analyzer` | `presidio_analyzer` | Default path needs a spaCy model, normally `en_core_web_lg`. |
| Text anonymization/deanonymization | `presidio-anonymizer` / `presidio_anonymizer` | `presidio_anonymizer` | None beyond Python package deps. |
| Combined text SDK | `presidio` | `presidio` plus analyzer/anonymizer packages | Same analyzer model requirement when default analyzer is used. |
| Structured DataFrame/JSON anonymization | `presidio-structured` / `presidio_structured` | `presidio_structured` | Pandas is installed by the package; analyzer model needed only when using default analysis builders. |
| Image and DICOM pixel redaction | `presidio-image-redactor` | `presidio_image_redactor` | Tesseract OCR binary for default local OCR; analyzer model for default analyzer path. |
| CLI scans | `presidio-cli` | `presidio_cli` | Default analyzer model for scans that use built-in NLP recognizers. |

Python support from package metadata and docs: Python 3.10 through 3.14.

## Minimal installs by task

```bash
# Text detection + anonymization with the default spaCy analyzer path
python -m pip install presidio-analyzer presidio-anonymizer
python -m spacy download en_core_web_lg

# Convenience meta package for analyzer + anonymizer
python -m pip install presidio
python -m spacy download en_core_web_lg

# Structured DataFrame/JSON workflows
python -m pip install presidio-structured
python -m spacy download en_core_web_lg  # only for default analysis builders

# Image/DICOM pixel redaction
python -m pip install presidio-image-redactor
python -m spacy download en_core_web_lg
# Also install the Tesseract OCR system binary for your OS.

# CLI file/directory scans
python -m pip install presidio-cli
python -m spacy download en_core_web_lg
```

PyPI normalizes hyphens and underscores. The project metadata and docs use both forms for analyzer/anonymizer packages; prefer the hyphenated names in new commands when possible.

## Optional extras and integrations

Install only the extra required by the selected workflow:

| Extra/integration | Install shape | When to use | Extra requirements |
| --- | --- | --- | --- |
| Analyzer server | `presidio-analyzer[server]` | Flask/Gunicorn analyzer REST service | Long-running service process. |
| Anonymizer server | `presidio-anonymizer[server]` | Flask/Gunicorn anonymizer REST service | Long-running service process. |
| Image server | `presidio-image-redactor[server]` if available for the release | Image redaction REST service | Tesseract for default OCR. |
| Transformers NLP engine | `presidio-analyzer[transformers]` | Hugging Face token-classification pipeline inside Analyzer | Small spaCy model such as `en_core_web_sm`; transformer model download/cache. |
| Stanza NLP engine | `presidio-analyzer[stanza]` | Stanza NER/token features | Stanza model download/cache. |
| GLiNER recognizer | `presidio-analyzer[gliner]` | GLiNER-based flexible entity recognizer | Model download/cache; optional ONNX runtime. |
| LangExtract / Ollama / Azure OpenAI | `presidio-analyzer[langextract]` | LLM/SLM recognizer workflows | Ollama service/model or Azure endpoint/API key. |
| Azure AI Language recognizer | `presidio-analyzer[azure-ai-language]` | Azure Text Analytics PII recognizer | Azure credentials and endpoint. |
| AHDS recognizer/surrogate | `presidio-analyzer[ahds]` or `presidio-anonymizer[ahds]` | Azure Health Data Services PHI de-identification | AHDS endpoint and Azure auth. |
| Azure Document Intelligence OCR | dependency is in image package base in this checkout | Cloud OCR backend for images/documents | Endpoint plus API key or Azure SDK credential. |

Do not install all extras by default. Many optional integrations require credentials, external services, model downloads, or GPU-capable packages.

## GPU guidance

Presidio's base workflows run on CPU. GPU is optional for selected NLP/model integrations such as Transformers, GLiNER, Stanza, and spaCy transformer models.

Use `PRESIDIO_DEVICE` only when a configured backend supports it:

```bash
export PRESIDIO_DEVICE=cpu
export PRESIDIO_DEVICE=cuda
export PRESIDIO_DEVICE=cuda:0
```

For NVIDIA spaCy acceleration, install a CuPy/spaCy CUDA variant matching the local CUDA runtime, for example `spacy[cuda12x]`. A visible GPU is not proof that the selected Presidio workflow is using it; verify with the framework-specific check described in `sub-skills/analyze-text/references/recognizers-and-nlp.md`.

## Installation checks

Run the bundled root checker after installation:

```bash
python scripts/check_presidio_install.py --help
python scripts/check_presidio_install.py
python scripts/check_presidio_install.py --smoke
```

If you intentionally use only pattern recognizers with `NoOpNlpEngine`, skip the model gate:

```bash
python scripts/check_presidio_install.py --skip-model-check --skip-tesseract-check
```

## Editable/source installs for contributors

For repo development, install the specific package directories in editable mode instead of using the public package commands. Keep that as local development context; do not require editable installs for ordinary Presidio SDK use.
