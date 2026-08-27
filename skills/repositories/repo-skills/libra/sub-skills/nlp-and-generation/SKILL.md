---
name: nlp-and-generation
description: "Use Libra for text classification, summarization, named entity
  recognition, GPT-2 text generation, image captioning, and NLTK/TextBlob
  runtime setup."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# NLP and Generation with Libra

Load this sub-skill when the task uses Libra's text and language-generation APIs: sentiment/text classification, summarization, GPT-2 text generation, named entity recognition, image captioning, vocabulary inspection, or NLTK/TextBlob runtime setup.

## What this sub-skill owns
- `text_classification_query(...)` and `classify_text(...)`
- `summarization_query(...)` and `get_summary(...)`
- `generate_text(...)`
- `named_entity_query(...)`
- `image_caption_query(...)` and `generate_caption(...)`
- NLTK corpora, TextBlob/POS-tagging assumptions, HuggingFace/TensorFlow model downloads, and NLP preprocessing helper behavior

## Trigger phrases
Use this route when a user asks to:
- train a sentiment or text classifier from a CSV and classify new text
- fine-tune or use summarization on text/summary pairs
- generate text from a file or prefix prompt
- detect named entities in a text column
- caption images from a CSV of image paths and captions
- fix missing NLTK corpora, TextBlob tagging, or HuggingFace model download failures

## Bundled references
- `references/api-reference.md` for methods, model keys, and parameters
- `references/workflows.md` for end-to-end recipes
- `references/data-formats.md` for text, summary, generation, NER, and captioning data shapes
- `references/runtime-setup.md` for NLTK, TextBlob, transformers, and optional GPU setup
- `references/troubleshooting.md` for common NLP/generation failures

## Bundled scripts
- `scripts/prepare_nltk_corpora.py` checks required corpora and can optionally download them when network access is explicitly allowed.
- `scripts/smoke_text_generation.py` checks the `generate_text` API surface without forcing a GPT-2 download by default.

## Operating notes
1. `client.__init__` downloads NLTK `punkt`, `averaged_perceptron_tagger`, and `stopwords`; patch it only for non-NLP smoke checks that do not need corpora.
2. `text_classification_query` defaults to label column `label`; `summarization_query` defaults to label column `summary`.
3. `generate_text(file_data=True)` reads the `client` dataset path as a text file. Use `file_data=False, prefix="..."` when the user wants prompt-only generation.
4. Transformer workflows load HuggingFace models and can require network/cache access. State this before running them.
5. Image captioning is owned here because the public API lives with the NLP queries, but image-path/layout debugging should also consult `sub-skills/vision-and-generative`.

## Cross-links
- Use the root skill for global install and pandas compatibility shims.
- Route tabular model selection and `analyze()`/plot workflows to `sub-skills/tabular-modeling` unless the model key is NLP-specific.
- Route image classification, CNN export, GANs, and image dataset layout checks to `sub-skills/vision-and-generative`.
