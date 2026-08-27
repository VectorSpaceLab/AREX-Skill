---
name: ml-metrics-and-translation
description: "Use NLTK classical ML, probability, language modeling, metrics,
  and translation/alignment APIs without reopening the source repo."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# NLTK ML, Metrics, and Translation

Use this sub-skill when a task needs NLTK's classical machine-learning, probability, n-gram language-modeling, evaluation metric, or machine-translation/alignment APIs.

## Route here for

- Feature-dictionary classifier workflows: `NaiveBayesClassifier`, `DecisionTreeClassifier`, `MaxentClassifier`, `SklearnClassifier`, classifier `accuracy`, `apply_features`, and `prob_classify` interpretation.
- Vector-space clustering with `KMeansClusterer`, `EMClusterer`, `GAAClusterer`, and NLTK distance helpers.
- Count/probability utilities: `FreqDist`, `ConditionalFreqDist`, `ProbDistI` implementations, and conditional probability distributions.
- N-gram language models: `padded_everygram_pipeline`, `Vocabulary`, `MLE`, `Lidstone`, `Laplace`, `WittenBellInterpolated`, `KneserNeyInterpolated`, `entropy`, `perplexity`, and unseen-word handling.
- Evaluation metrics: `precision`, `recall`, `f_measure`, `accuracy`, edit/label distances, segmentation metrics, association measures, agreement, confusion matrices, and translation scores.
- Translation/alignment: `Alignment`, `AlignedSent`, IBM Models 1-5, `PhraseTable`, BLEU/GLEU/CHRF/NIST/METEOR/RIBES/LEPOR, and alignment error rate.

## Route elsewhere first

- If the user is blocked by missing corpora or wants downloads/data paths, use the sibling data/downloader guidance first.
- If the user needs tokenization, POS tags, stemming, lemmatization, or sentiment feature extraction before modeling, use the preprocessing sibling first.
- If parse trees, grammars, chunking, dependency graphs, semantics, or inference are the main task, use the parsing/semantics sibling first.

## Read the linked files

- Start with [references/api-reference.md](references/api-reference.md) for public API contracts, required input shapes, optional dependencies, and score semantics.
- Use [references/workflows.md](references/workflows.md) for task recipes that combine classifiers, probability utilities, LMs, metrics, and alignments.
- Use [references/troubleshooting.md](references/troubleshooting.md) when imports, feature dictionaries, smoothing, metric edge cases, optional binaries, or alignments fail.
- Run [scripts/ml_translate_smoke.py](scripts/ml_translate_smoke.py) for a tiny deterministic no-download smoke check in any environment where NLTK and its base dependencies are installed.

## Operating rules

1. Keep examples tiny unless the user explicitly provides corpora or vectors. Many NLTK examples in the upstream tests use downloadable corpora; do not imply those are available.
2. Prefer pure-Python/base workflows first. Treat `numpy`, `scipy`, `scikit-learn`, `python-crfsuite`, MEGAM/TADM, Graphviz, Java wrappers, and corpora as optional unless the task requires them.
3. For classifiers, verify the user's data is `[(featureset_dict, label), ...]` and that prediction inputs are `featureset_dict` values, not raw strings or token lists.
4. For language models, make padding, vocabulary cutoff, smoothing, and `<UNK>` behavior explicit before interpreting entropy/perplexity.
5. For translation metrics and alignment models, confirm tokenized inputs and alignment index direction before scoring.
