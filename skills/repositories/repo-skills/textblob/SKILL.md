---
name: textblob
description: "Use TextBlob for Python text processing: tokenization, POS
  tagging, noun phrases, sentiment, lexical tools, classifiers, and extensions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TextBlob repo skill

Use this repo skill when a task names TextBlob or asks for a simple Python NLP
workflow involving raw text, tokens, sentences, part-of-speech tags, noun
phrases, sentiment, spelling, WordNet, word morphology, text classifiers, or
TextBlob-compatible custom models.

Do not use this skill for large neural NLP training, transformer pipelines,
spaCy pipeline components, annotation platforms, or LLM evaluation unless the
request specifically needs TextBlob interoperability.

## Setup first

TextBlob installs as a Python package, but many workflows require NLTK corpus
data at runtime. In the target environment, a typical setup is:

```bash
python -m pip install -U textblob
python -m textblob.download_corpora lite   # default models and common basics
# Use the full command when ConllExtractor or NaiveBayesAnalyzer is needed:
python -m textblob.download_corpora
```

Minimal import and corpus diagnostic:

```bash
python scripts/check_textblob_setup.py --json
python scripts/check_textblob_setup.py --require-all-corpora
```

Read [corpora and setup](references/corpora-and-setup.md) before debugging a
`MissingCorpusError`, optional `numpy` issue, or corpus-backed workflow.

## Route by task

| User request | Read |
| --- | --- |
| Tokenize text, split sentences, tag POS, extract noun phrases, compute sentiment, parse, count words/phrases, serialize sentence records, or use `Blobber` with built-in models | [core NLP workflows](sub-skills/core-nlp-workflows/SKILL.md) |
| Singularize/pluralize words, stem, lemmatize, correct spelling, inspect WordNet synsets/definitions, or normalize word lists | [word and lexical tools](sub-skills/word-and-lexical-tools/SKILL.md) |
| Train/evaluate/update Naive Bayes, Decision Tree, MaxEnt, or Positive Naive Bayes classifiers; load CSV/JSON/TSV training data; write feature extractors; register data formats | [classifiers and data formats](sub-skills/classifiers-and-data-formats/SKILL.md) |
| Implement custom tokenizers, POS taggers, NP extractors, sentiment analyzers, parsers, language/model extensions, or shared `Blobber` factories | [custom models and extensions](sub-skills/custom-models-and-extensions/SKILL.md) |

Shared references:

- [API map](references/api-map.md): package/module routing and public API
  family overview.
- [Corpora and setup](references/corpora-and-setup.md): install commands,
  corpus names, optional dependencies, and setup verification.
- [Troubleshooting](references/troubleshooting.md): cross-cutting install,
  import, corpus, and version issues.
- [Repository provenance](references/repo-provenance.md): source snapshot used
  to build this skill and refresh criteria.

## Common decision points

- If raw text still needs tokenization, sentence splitting, tags, sentiment, or
  noun phrases, start with the core NLP sub-skill before moving to word-level or
  classifier workflows.
- If a classifier task includes file formats, labels, updates, or feature
  extraction, use the classifier sub-skill even if the final classifier is used
  through `TextBlob(..., classifier=cl)`.
- If a request says "custom tokenizer/tagger/analyzer/parser" or mentions an
  extension package, use the custom-model sub-skill for interface validation,
  then return to core NLP for ordinary `TextBlob` usage.
- If a workflow fails only because corpus data is absent, do not change model
  selection silently. Run explicit corpus setup in the target environment and
  rerun the relevant smoke script.

## Quick sanity examples

```python
from textblob import TextBlob, Word

blob = TextBlob("TextBlob is amazingly simple. Great fun!")
print(blob.sentiment)
print([(str(word), tag) for word, tag in blob.tags])
print(blob.noun_phrases)

print(Word("speling").correct())
```

Classifier example:

```python
from textblob import TextBlob
from textblob.classifiers import NaiveBayesClassifier

train = [("I love this", "pos"), ("This is awful", "neg")]
cl = NaiveBayesClassifier(train)
blob = TextBlob("I love this API. This bug is awful.", classifier=cl)
for sentence in blob.sentences:
    print(sentence, sentence.classify())
```

When these examples fail, first run `python scripts/check_textblob_setup.py` and
then follow the nearest sub-skill troubleshooting reference.
