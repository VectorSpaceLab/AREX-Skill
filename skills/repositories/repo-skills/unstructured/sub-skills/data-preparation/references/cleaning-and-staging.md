# Cleaning and Staging Reference

## Cleaner Selection

| Need | Use | Notes |
| --- | --- | --- |
| Collapse whitespace and line breaks | `clean_extra_whitespace()` or `clean(..., extra_whitespace=True)` | Converts `\xa0` and newlines to spaces, collapses repeated spaces, strips edges. |
| Remove leading bullets | `clean_bullets()` or `clean(..., bullets=True)` | Removes only bullet-like markers at the start of the string. |
| Remove outline prefixes | `clean_ordered_bullets()` | Handles short dot-delimited numeric/alphanumeric prefixes such as `1.`, `1.1`, `D.b.C`; leaves long/non-outline prefixes alone. |
| Normalize ligatures | `clean_ligatures()` | Converts common Unicode ligatures and historic characters to text equivalents. |
| Fix quote/dash mojibake | `replace_unicode_quotes()` | Handles common SEC/email-style quote and dash encodings. |
| Decode MIME quoted-printable fragments | `replace_mime_encodings(text, encoding="utf-8")` | Use the source encoding when known; wrong encodings can preserve mojibake. |
| Remove punctuation | `remove_punctuation()` or `remove_sentence_punctuation()` | Useful before matching or deduping, but destructive for annotation offsets. |
| Remove anchored labels | `clean_prefix()` / `clean_postfix()` | Pattern is a regex anchored at the start/end. Escape literal punctuation. |
| Preserve offset mapping after whitespace cleanup | `clean_extra_whitespace_with_index_run()` | Returns cleaned text and an index-shift array for offset repair. |

For annotation workflows, clean before creating offsets. If entity offsets already exist, either avoid destructive cleaners or recompute offsets after cleanup.

## Extraction Helpers

`unstructured.cleaners.extract` contains local regex helpers:

```python
from unstructured.cleaners.extract import (
    extract_datetimetz,
    extract_email_address,
    extract_image_urls_from_html,
    extract_ordered_bullets,
    extract_text_before,
)

sender_emails = extract_email_address(header_text)
first_section = extract_text_before(document_text, r"\nAPPENDIX\b")
ordered_parts = extract_ordered_bullets("5.3.1 Convolutional Networks")
```

`extract_text_before()` and `extract_text_after()` select a match by zero-based `index`. They raise `ValueError` for negative indexes or when the requested occurrence is missing.

## Annotation Staging Matrix

| Target | Function | Output shape | Important validation |
| --- | --- | --- | --- |
| Prodigy JSON | `stage_for_prodigy(elements, metadata=None)` | List of `{"text": ..., "meta": ...}` | Metadata length must match elements; metadata cannot include `id`. |
| Prodigy CSV | `stage_csv_for_prodigy(elements, metadata=None)` | CSV text with `text`, `id`, and metadata columns | Metadata keys are lowercased in rows. |
| Label Studio | `stage_for_label_studio(...)` | List of tasks with `data`, optional `annotations`, optional `predictions` | Annotation/prediction outer lists must match elements; label type must be valid; prediction score is `0..1`; package marks this function deprecated. |
| Labelbox | `stage_for_label_box(elements, output_directory, url_prefix, ...)` | Writes text files and returns import config | Output directory must exist unless `create_directory=True`; external ids and attachments must match element count. |
| Datasaur | `stage_for_datasaur(elements, entities=None)` | List of `{"text": ..., "entities": [...]}` | Entity list length must match elements; entity keys are `text`, `type`, `start_idx`, `end_idx`. |
| Baseplate | `stage_for_baseplate(elements)` | `{"rows": [{"data": ..., "metadata": ...}]}` | Nested element and metadata dictionaries are flattened for API columns. |
| Hugging Face | `stage_for_transformers(elements, tokenizer, **chunk_kwargs)` | Elements split to tokenizer attention windows | Requires a tokenizer; buffer must be non-negative and smaller than max input size. |

## Concrete Staging Examples

Prodigy with extra metadata:

```python
from unstructured.staging.prodigy import stage_for_prodigy

metadata = [{"source": "support-ticket", "priority": "high"} for _ in elements]
records = stage_for_prodigy(elements, metadata=metadata)
```

Label Studio classification prediction:

```python
from unstructured.staging.label_studio import (
    LabelStudioPrediction,
    LabelStudioResult,
    stage_for_label_studio,
)

prediction = LabelStudioPrediction(
    result=[
        LabelStudioResult(
            type="choices",
            value={"choices": ["Positive"]},
            from_name="sentiment",
            to_name="text",
        )
    ],
    score=0.82,
)
tasks = stage_for_label_studio(elements, predictions=[[prediction] for _ in elements])
```

Datasaur NER entities:

```python
from unstructured.staging.datasaur import stage_for_datasaur

entities = [[{"text": "Acme", "type": "ORG", "start_idx": 0, "end_idx": 4}] for _ in elements]
rows = stage_for_datasaur(elements, entities=entities)
```

Labelbox with hosted text-file URLs:

```python
from unstructured.staging.label_box import stage_for_label_box

config = stage_for_label_box(
    elements,
    output_directory="labelbox-text",
    url_prefix="https://storage.example.com/labelbox-text",
    external_ids=[element.id for element in elements],
    create_directory=True,
)
```

The returned `data` URLs are references to where the text files will be available. The function writes local files but does not upload them or authenticate to Labelbox.

## Hugging Face Attention Window Preparation

Use `stage_for_transformers()` when a downstream model tokenizer has a smaller context window than an element's text:

```python
from unstructured.staging.huggingface import stage_for_transformers
from unstructured.nlp.tokenize import sent_tokenize

prepared = stage_for_transformers(
    elements,
    tokenizer,
    buffer=8,
    split_function=sent_tokenize,
)
```

If any split segment alone exceeds the tokenizer limit, `chunk_by_attention_window()` raises `ValueError`. Choose a finer `split_function` or increase the model context window.

## NLP Helpers

```python
from unstructured.nlp.tokenize import pos_tag, sent_tokenize, word_tokenize

sentences = sent_tokenize(text)
tokens = word_tokenize(text)
tags = pos_tag(text)
```

These helpers cache results and load a spaCy English model. First use may be slower than pure-regex cleaners and may need model installation permissions or network access if the model is missing.

## Translation Caveat

```python
from unstructured.cleaners.translate import translate_text

english = translate_text(text, source_lang="de", target_lang="en")
```

Translation is not a simple local cleaner. It depends on `langdetect`, `transformers`, Marian tokenizer/model loading, and a supported Hugging Face `Helsinki-NLP/opus-mt-<source>-<target>` model. It may download model weights and can fail with `ValueError` when the language code is invalid or the source/target pair is unsupported.
