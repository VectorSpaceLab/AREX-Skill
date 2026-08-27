# Data formats and conversion

spaCy trains on annotated `Doc` objects serialized in `.spacy` files. Most workflows either create `DocBin` files directly or use `spacy convert` to transform existing annotations into that format.

## Core objects

- `DocBin` is the binary container that stores `Doc` objects in `.spacy` files.
- `Example` holds one reference/prediction pair for training and evaluation.
- `Corpus(path)` reads `.spacy` files and yields `Example` objects.
- `JsonlCorpus(path)` reads raw-text JSONL files and yields `Example` objects for pretraining.

## Recommended training-data path

```python
import spacy
from spacy.tokens import DocBin

nlp = spacy.blank("en")
docbin = DocBin()

for text, cats in [("Great product.", {"POSITIVE": 1.0, "NEGATIVE": 0.0})]:
    doc = nlp.make_doc(text)
    doc.cats = cats
    docbin.add(doc)

docbin.to_disk("train.spacy")
```

For NER-style annotations, create spans with `Doc.char_span(...)` and only add spans that align to token boundaries.

## Supported `spacy convert` inputs

| Input | Typical use | Notes |
| --- | --- | --- |
| `.conll` / `.ner` | CoNLL-style token-per-line or IOB NER data. | Sentence boundaries can be inferred with `--seg-sents` and a base model or blank tokenizer. |
| `.iob` | Sentence-per-line IOB text. | Supports `word|TAG|IOB` and `word|IOB` shapes. |
| `.conllu` | Universal Dependencies data. | Use `--merge-subtokens` and `--morphology` when needed. |
| `.json` | Legacy spaCy v2 JSON training data. | Deprecated. Convert to `.spacy` for new workflows. |
| Directory input | Batch conversion. | `auto` detects file type by extension and content. Mixed file types in one directory are rejected. |

## Useful `spacy convert` flags

- `--file-type spacy` is the default and is the right choice for training.
- `--file-type json` only exists for the legacy v2 JSON format.
- `--converter auto|json|conllu|conll|ner|iob` selects or detects the reader.
- `--n-sents` groups sentences into documents.
- `--seg-sents` enables sentence segmentation for formats that need it.
- `--base` / `--model` provides a base pipeline for sentence segmentation.
- `--morphology` appends morphology in CoNLL-U conversion.
- `--merge-subtokens` merges CoNLL-U subtokens.
- `--ner-map` remaps NER labels in CoNLL-U input.
- `--concatenate` writes one combined output file.

## Manual conversion recipes

### NER offsets to `.spacy`

```python
import spacy
from spacy.tokens import DocBin

nlp = spacy.blank("en")
docbin = DocBin()

doc = nlp("Apple is looking at buying U.K. startup.")
span = doc.char_span(0, 5, label="ORG", alignment_mode="strict")
if span is None:
    raise ValueError("offsets do not align with tokenization")
doc.ents = [span]
docbin.add(doc)
docbin.to_disk("train.spacy")
```

### Textcat JSONL to `.spacy`

A textcat JSONL record usually looks like `{"text": "...", "cats": {...}}`. Use the bundled converter script in this sub-skill when you need a tiny safe conversion without downloads.

### Example objects

If you need a custom training example in Python, build it with `Example.from_dict(doc, gold_dict)` and then create a `DocBin` from the reference docs. `Corpus` and `JsonlCorpus` are the default readers that turn those stored annotations back into `Example` objects during training or pretraining.

## Legacy note on `docs_to_json`

`spacy.training.docs_to_json` is a legacy helper for the old v2 JSON training format. Keep it only for backward-compatibility or old fixtures. For current spaCy training and evaluation, prefer `.spacy` / `DocBin`.

## Bundled textcat converter script

Run the bundled helper when you have a small textcat JSONL file with text and categories and want a `.spacy` file for training or debugging without depending on a pretrained model.

```bash
python scripts/convert_textcat_jsonl_to_docbin.py --input-file tiny.jsonl --output-file train --lang en --limit 10
```

The script writes `train.spacy` when the output path has no suffix, and it can optionally load an installed model or add sentence boundaries for blank-tokenizer runs.
