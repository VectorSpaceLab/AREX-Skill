---
name: data-preparation
description: "Clean extracted text, stage Unstructured elements for annotation
  and labeling tools, use lightweight NLP helpers, and prepare local outputs for
  downstream systems. Route raw partitioning to partitioning, generic element
  JSON/schema work to elements-and-metadata, provider embeddings to embeddings,
  and chunk composition to chunking."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data Preparation

Use this sub-skill when a task starts from text or already-partitioned Unstructured elements and needs local cleanup, annotation export, lightweight tokenization, or preparation for downstream systems. Do not use it to partition raw source files, design embeddings providers, or inspect the full element JSON schema.

## Start Here

- For OCR or PDF-extracted text cleanup, use `unstructured.cleaners.core` first; these helpers are local and deterministic.
- For metadata extraction from email-like text or HTML snippets, use `unstructured.cleaners.extract` regular-expression helpers.
- For annotation tools, stage existing text elements with `unstructured.staging.prodigy`, `label_studio`, `label_box`, `datasaur`, `baseplate`, or `huggingface` after confirming each target tool's schema.
- For tokenization and sentence splitting, use `unstructured.nlp.tokenize` only when the environment can load the spaCy model; first use may install or load model data.
- Treat translation, Hugging Face tokenizers/models, annotation SaaS APIs, and hosted storage URLs as third-party/service boundaries; require explicit dependencies, network access, and credentials where applicable.

## Local Text Cleaning

Use the combined `clean()` function for simple normalization:

```python
from unstructured.cleaners.core import clean

normalized = clean(
    raw_text,
    extra_whitespace=True,
    dashes=True,
    bullets=True,
    trailing_punctuation=True,
)
```

Use focused cleaners when order matters or when a single transform is safer:

- `clean_extra_whitespace()` collapses newlines, non-breaking spaces, and repeated spaces.
- `clean_bullets()` removes a leading Unicode bullet only, preserving bullets elsewhere.
- `clean_ordered_bullets()` removes numeric/alphanumeric outline prefixes such as `1.1` when they look like section markers.
- `clean_ligatures()` maps common ligatures such as `ﬁ` and `ﬂ` to ASCII-style text.
- `replace_unicode_quotes()` fixes common mojibake quote/dash sequences; `replace_mime_encodings()` decodes quoted-printable MIME fragments.
- `clean_prefix()` and `clean_postfix()` remove anchored regex patterns from text edges.

For a safe command-line preview, use the bundled script:

```bash
python sub-skills/data-preparation/scripts/clean_text_preview.py --text "●  RISK\u00a0FACTORS---"
python sub-skills/data-preparation/scripts/clean_text_preview.py input.txt --json-output preview.json
python sub-skills/data-preparation/scripts/clean_text_preview.py elements.json --elements-json --max-items 5
```

The script reads local text or Unstructured element JSON, applies selected local cleaners, and writes a preview. It does not call partition APIs, translation models, hosted services, or annotation APIs.

## Extraction Helpers

Use `unstructured.cleaners.extract` for lightweight pattern extraction:

```python
from unstructured.cleaners.extract import extract_email_address, extract_text_after

emails = extract_email_address(header_text)
body = extract_text_after(raw_email, r"\n\n", index=0)
```

Common helpers include `extract_email_address()`, `extract_ip_address()`, `extract_ip_address_name()`, `extract_mapi_id()`, `extract_datetimetz()`, `extract_us_phone_number()`, `extract_ordered_bullets()`, and `extract_image_urls_from_html()`. `extract_text_before()` and `extract_text_after()` raise `ValueError` if the requested match index does not exist; catch that when patterns are optional.

## Annotation Staging Routes

Work from `Text`-like elements (`Title`, `NarrativeText`, `Text`, etc.) whenever an annotation target expects plain text examples:

```python
from unstructured.staging.prodigy import stage_for_prodigy

records = stage_for_prodigy(elements, metadata=[{"source": "batch-a"} for _ in elements])
```

- Prodigy: `stage_for_prodigy()` emits JSON-like records with `text` and `meta`; `stage_csv_for_prodigy()` emits CSV. Do not pass an `id` key in metadata because element ids are injected into `meta.id`.
- Label Studio: `stage_for_label_studio()` emits task dictionaries under `data`; optional annotations/predictions must match element count. `LabelStudioResult.type` must be one of the module's supported label types, and prediction `score` must be between `0` and `1`. This function is deprecated in the package, so prefer validating against current Label Studio tooling before production use.
- Labelbox: `stage_for_label_box()` writes one text file per element and returns import config with `data` URLs. It requires an output directory and a URL prefix where those files will be hosted; attachment `type` must be `IMAGE`, `VIDEO`, `RAW_TEXT`, `TEXT_URL`, or `HTML`.
- Datasaur: `stage_for_datasaur()` emits `text` plus `entities`; each entity requires `text`, `type`, `start_idx`, and `end_idx`, and the entity list length must match the elements length.
- Baseplate: `stage_for_baseplate()` flattens element dictionaries into `rows` with `data` and `metadata` fields suitable for API upload payloads.
- Hugging Face/transformers: `stage_for_transformers()` and `chunk_by_attention_window()` split long text to fit a provided tokenizer's attention window. This requires a tokenizer object and the `transformers` dependency.

See `references/cleaning-and-staging.md` for schema examples and `references/troubleshooting.md` for common validation failures.

## NLP and Translation Boundaries

`unstructured.nlp.tokenize.sent_tokenize()`, `word_tokenize()`, and `pos_tag()` use spaCy under the hood with caching. They may load or install a pinned `en_core_web_sm` model on first use, so do not assume they are zero-dependency helpers in locked-down or offline environments.

`unstructured.cleaners.translate.translate_text()` uses `langdetect`, `transformers`, Marian tokenizer/model loading, and Hugging Face model names such as `Helsinki-NLP/opus-mt-de-en`. It returns unchanged text when the source and target language are the same or when text is blank, but actual translation can require large model downloads, network access, and supported source/target language pairs. Ask before enabling it in offline, credential-sensitive, or latency-sensitive workflows.

## Boundaries

- Raw document partitioning and document-specific parser options belong to `partitioning`.
- Element schema inspection, generic JSON/NDJSON/Markdown/Text conversion, metadata coordinates, and table fidelity belong to `elements-and-metadata`.
- Chunk construction with `chunk_elements()` or `chunk_by_title()` belongs to `chunking`; this sub-skill only covers Hugging Face attention-window staging.
- Provider embeddings, embedding interfaces, and vector output preparation belong to `embeddings`.
- Review/test artifacts do not belong in this runtime subtree.

## Evidence

This sub-skill is grounded in the package cleaner, staging, and NLP helper modules plus their behavior tests.
