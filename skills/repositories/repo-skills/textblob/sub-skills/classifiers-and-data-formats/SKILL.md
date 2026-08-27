---
name: classifiers-and-data-formats
description: "Build, evaluate, update, and debug TextBlob classifiers and their
  CSV, JSON, TSV, and custom training data formats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TextBlob classifiers and data formats

Use this sub-skill when the task is about training, evaluating, updating, or debugging a `textblob.classifiers` classifier, or when classifier training/test data must be loaded from CSV, JSON, TSV, or a registered custom format.

## Bundled resources

- [Classifier workflows](references/classifier-workflows.md): recipes for training, evaluating, updating, TextBlob sentence classification, Positive Naive Bayes, MaxEnt, feature extractors, and difficult mixed-format cases.
- [Data formats](references/data-formats.md): CSV/JSON/TSV schemas, automatic detection, registry usage, and custom format registration.
- [API reference](references/api-reference.md): constructor signatures, methods, return shapes, and caveats.
- [Troubleshooting](references/troubleshooting.md): malformed train sets, missing corpora, file-like mistakes, unknown formats, classifier injection errors, and feature-extractor debugging.
- [Classifier smoke script](scripts/classifier_smoke.py): tiny in-memory and temporary-file classifier/data-format checks. Run `python scripts/classifier_smoke.py --help`.

## Covered capabilities

- Classifiers: `NaiveBayesClassifier`, `DecisionTreeClassifier`, `MaxEntClassifier`, `PositiveNaiveBayesClassifier`, and `NLTKClassifier` wrappers.
- Feature extractors: `basic_extractor`, `contains_extractor`, and custom one-argument or two-argument extractors.
- Training/evaluation data shapes: in-memory `[(text_or_tokens, label), ...]`, opened file-like data, CSV `text,label`, JSON arrays with `text` and `label`, TSV, and custom registered formats.
- Classifier operations: `classify`, `prob_classify`, `accuracy`, `update`, `labels`, `informative_features`, `show_informative_features`, `pretty_format`, and `pseudocode`.
- `TextBlob(..., classifier=cl)` workflows, including sentence-level `.classify()` on blobs created with the same classifier.
- `textblob.formats.detect`, `get_registry`, `register`, and common `FormatError` / `ValueError` handling.

## Route elsewhere

- `NaiveBayesAnalyzer` as a sentiment analyzer is covered by [core NLP workflows](../core-nlp-workflows/SKILL.md). It is classifier-backed, but its operating surface is `TextBlob(..., analyzer=NaiveBayesAnalyzer()).sentiment`, not custom classifier training.
- Writing reusable base interfaces, extension packages, custom model classes, or language-package integrations belongs in [custom models and extensions](../custom-models-and-extensions/SKILL.md). This sub-skill only covers classifier feature extractors and file-format registration needed for classifier data.

## Operating workflow

1. **Choose the classifier.** Use Naive Bayes for a small reliable default, Decision Tree when explainable tree output is needed, MaxEnt only when its slower NLTK training is acceptable, Positive Naive Bayes for one-positive-class plus unlabeled data, and `NLTKClassifier` only when wrapping a concrete `nltk.classify` class.
2. **Normalize data before training.** Prefer a list of `(document, label)` pairs where `document` is either a string or a list of tokens. Keep labels consistent (`"pos"`/`"neg"`, booleans, or other labels, but not a mixture unless that is intentional).
3. **Use file-like inputs correctly.** Open CSV/JSON/TSV files yourself and pass the file object, not a filename string. Let TextBlob detect simple files or pass `format="csv"`, `"json"`, or `"tsv"` explicitly for reliability.
4. **Train and validate.** Call `classify()` on known examples, `accuracy()` on held-out data, and `labels()` to confirm the label set. For Naive Bayes or MaxEnt, use `prob_classify()` when probabilities matter.
5. **Update deliberately.** `update()` expects normalized in-memory examples. If new data arrives as CSV/JSON/TSV, parse it into a list first, validate labels, then call `update()`.
6. **Integrate with TextBlob.** Pass `classifier=cl` to `TextBlob` or `Blobber`; then `blob.classify()` classifies the full blob and each sentence object created from that blob shares the same classifier.
7. **Inspect or explain.** Use Naive Bayes `informative_features()` / `show_informative_features()` or Decision Tree `pretty_format()` / `pseudocode()` when a user needs reasons, audits, or debugging clues.

If a workflow fails, first check the symptom table in [troubleshooting](references/troubleshooting.md), then inspect the exact data schema in [data formats](references/data-formats.md). Use the bundled smoke script for a package-level sanity check:

```bash
python scripts/classifier_smoke.py --json
python scripts/classifier_smoke.py --skip-decision-tree
```

