---
name: core-nlp-workflows
description: "Use TextBlob document-level NLP workflows for tokenization,
  sentence splitting, POS tags, noun phrases, sentiment, parsing, counts, and
  Blobber routing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TextBlob core NLP workflows

Use this sub-skill when a task starts from raw text and needs TextBlob's
high-level document or sentence APIs: `TextBlob`, `Sentence`, `Blobber`, words,
tokens, sentences, POS tags, noun phrases, sentiment, parsing, n-grams, counts,
JSON serialization, or built-in model overrides.

Route elsewhere when the request is mostly about:

- Word-level spelling, inflection, lemmatization, stemming, WordNet, or
  `WordList` batch transforms: `../word-and-lexical-tools/SKILL.md`.
- Classifier training/evaluation, training data files, feature extractors, or
  `TextBlob(..., classifier=...)`: `../classifiers-and-data-formats/SKILL.md`.
- Writing custom model classes, extension packages, or reusable `Blobber`
  factories with custom components: `../custom-models-and-extensions/SKILL.md`.

## Bundled resources

- [Workflows](references/workflows.md): task-oriented recipes for tokenization,
  tagging, noun phrases, sentiment, parsing, counts, JSON, and `Blobber`.
- [API reference](references/api-reference.md): verified signatures, defaults,
  return shapes, and model classes for document-level APIs.
- [Troubleshooting](references/troubleshooting.md): missing NLTK corpora,
  punctuation/tokenization surprises, slow corpus-backed models, and analyzer
  or parser misuse.
- [Core NLP smoke script](scripts/core_nlp_smoke.py): read-only installed
  package checks. Run `python scripts/core_nlp_smoke.py --help`.

## Operating workflow

1. **Confirm setup.** TextBlob import alone is not enough for corpus-backed
   workflows. If tags, sentence splitting, noun phrases, lemmatization, or the
   Naive Bayes sentiment analyzer are needed, ensure the installed environment
   has TextBlob corpora. The parent skill links a setup reference and a root
   setup diagnostic.
2. **Create a blob.** Use `TextBlob(text)` for ordinary raw text. The
   constructor validates tokenizer, POS tagger, NP extractor, analyzer, and
   parser objects when custom ones are supplied.
3. **Choose the right property.**
   - Use `.sentences` for `Sentence` objects and sentence-level processing.
   - Use `.words` for word tokens without punctuation.
   - Use `.tokens` or `.tokenize(tokenizer)` when punctuation or a custom
     tokenizer contract matters.
   - Use `.tags`/`.pos_tags` for flattened POS tags across sentences.
   - Use `.noun_phrases` for normalized lowercase noun phrase strings.
   - Use `.sentiment`, `.polarity`, `.subjectivity`, or
     `.sentiment_assessments` for built-in sentiment workflows.
   - Use `.parse()` for the pattern-style parse string.
   - Use `.word_counts`, `.np_counts`, and `.ngrams(n)` for simple counts and
     phrase windows.
4. **Use `Blobber` when models should be shared.** `Blobber(...)` creates
   `TextBlob` instances that reuse the same tokenizer, tagger, extractor,
   analyzer, parser, and classifier objects. This is useful for expensive or
   configured models; route to the custom-model sub-skill when implementing the
   components themselves.
5. **Validate with a tiny smoke.** Run the bundled smoke script before relying
   on a new environment or after debugging corpus paths. Use
   `--skip-corpus-heavy` only when POS, sentences, and noun phrases are not part
   of the task.
6. **Keep downstream outputs explicit.** TextBlob properties are convenient and
   often cached. When building pipelines, record which property produced each
   field, whether punctuation was kept, and whether corpora or optional models
   were required.

## Quick patterns

```python
from textblob import Blobber, TextBlob
from textblob.sentiments import NaiveBayesAnalyzer
from textblob.tokenizers import WordTokenizer

blob = TextBlob("TextBlob is amazingly simple. Great fun!")
[str(s) for s in blob.sentences]
[(str(word), tag) for word, tag in blob.tags]
blob.noun_phrases
blob.sentiment.polarity
blob.ngrams(2)

# Discrete sentiment analyzer trained from movie_reviews corpus.
TextBlob("I love this library", analyzer=NaiveBayesAnalyzer()).sentiment

# Shared model factory.
tb = Blobber(tokenizer=WordTokenizer())
first = tb("one text")
second = tb("another text")
assert first.tokenizer is second.tokenizer
```

If `.tags`, `.sentences`, or `.noun_phrases` raises `MissingCorpusError`, do not
silently switch algorithms. Use [references/troubleshooting.md](references/troubleshooting.md)
to identify the missing corpus and run the explicit setup command in the target
environment.
