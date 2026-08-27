# Workflows

## Purpose

Use this when you need to assemble or adapt a scispaCy text-processing pipeline.

## 1) Biomedical pipeline with custom tokenizer and sentence segmentation

Start from a spaCy model such as `en_core_sci_sm`:

```python
import spacy
import scispacy.abbreviation
import scispacy.hyponym_detector
from scispacy.custom_tokenizer import combined_rule_tokenizer
from scispacy.custom_sentence_segmenter import pysbd_sentencizer

nlp = spacy.load("en_core_sci_sm")
nlp.tokenizer = combined_rule_tokenizer(nlp)
nlp.add_pipe("pysbd_sentencizer", first=True)
```

Use this pattern when biomedical punctuation, hyphenation, or line breaks need scispaCy tokenization rules.

## 2) Abbreviation detection

```python
nlp.add_pipe("abbreviation_detector", config={"make_serializable": False})
doc = nlp("Spinal and bulbar muscular atrophy (SBMA) is a disease.")
```

Tips:

- Import `scispacy.abbreviation` before adding the pipe so the factory exists.
- Turn on `make_serializable=True` when the document must be serialized or processed across workers.
- The detector stores the abbreviation span in `Doc._.abbreviations` and the long form in `Span._.long_form`.

## 3) Hyponym detection

```python
nlp.add_pipe("hyponym_detector", last=True, config={"extended": True})
doc = nlp("Keystone plant species such as fig trees are important.")
```

Notes:

- `extended=True` enables the larger Hearst-pattern set.
- The detector writes `Doc._.hearst_patterns`.
- It expects a parsed spaCy document; use a full pipeline model rather than a blank tokenizer-only pipeline.

## 4) Pretokenized input

For BIO-style or already segmented text, replace the tokenizer:

```python
from scispacy.util import WhitespaceTokenizer

nlp = spacy.load("en_core_web_sm")
nlp.tokenizer = WhitespaceTokenizer(nlp.vocab)
```

Use this only when token boundaries are already authoritative.

## 5) End-to-end smoke

The bundled `scripts/smoke_scispacy.py --mode components` command exercises all of the above with small sample texts. Run it after installation or after changing the component wiring.

## When to stop and check troubleshooting

Read the troubleshooting reference if you see:

- a missing factory registration error,
- a `doc.to_bytes()` failure after abbreviation detection,
- unexpected sentence boundaries around abbreviations or newlines,
- or a model-version mismatch warning.
