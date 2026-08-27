# API Reference: NLTK ML, Metrics, and Translation

This reference distills NLTK 3.10.x public contracts for classical ML, probability, language modeling, metrics, and translation/alignment. Examples are deliberately no-download unless marked as corpus-dependent.

## Classifier contracts

### Common interface

| API | Contract | Notes |
| --- | --- | --- |
| `ClassifierI.labels()` | Return the finite list of labels. | Labels are usually strings/ints but can be any immutable values. |
| `classify(featureset)` / `classify_many(featuresets)` | Predict labels from feature dictionaries. | A featureset is a `dict` mapping feature names to booleans, numbers, strings, or other stable feature values. |
| `prob_classify(featureset)` / `prob_classify_many(featuresets)` | Return `ProbDistI` objects over labels. | Not every classifier implements probabilities; `DecisionTreeClassifier.prob_classify*` can raise `NotImplementedError`. |
| `nltk.classify.accuracy(classifier, gold)` | Fraction correct over `gold=[(featureset, label), ...]`. | Empty gold returns `0`. |
| `apply_features(feature_func, toks, labeled=None)` | Lazily convert tokens to featuresets. | With labeled tokens, values become `(feature_func(tok), label)`. Useful for corpus readers. |

Training data shape is always the first thing to validate:

```python
train = [({"contains-good": True, "length": 4}, "pos"), ({"contains-good": False}, "neg")]
featureset = {"contains-good": True, "length": 2}
```

Do not pass a raw string, a token list, or `(token, label)` pairs directly to classifier training unless a feature extractor has already converted tokens into feature dictionaries.

### Naive Bayes

- Train with `NaiveBayesClassifier.train(labeled_featuresets, estimator=ELEProbDist)`.
- `labeled_featuresets` is `[(featureset_dict, label), ...]`.
- The classifier estimates `P(label)` and `P(feature_name=feature_value | label)`.
- A feature name never seen during training is ignored at classification time rather than forcing all labels to probability zero.
- Missing feature values in training are modeled with an implicit `None`; avoid using `None` as one of your own feature values.
- Use `classifier.prob_classify(fs).prob(label)` for label probabilities and `classifier.most_informative_features(n)` or `show_most_informative_features(n)` for feature interpretation.

Minimal pattern:

```python
from nltk.classify import NaiveBayesClassifier, accuracy

train = [({"word:good": True}, "pos"), ({"word:bad": True}, "neg")]
clf = NaiveBayesClassifier.train(train)
label = clf.classify({"word:good": True})
score = accuracy(clf, train)
```

### Decision tree, MaxEnt, and sklearn wrappers

| API | Use when | Dependency/caveat |
| --- | --- | --- |
| `DecisionTreeClassifier.train(train, entropy_cutoff=..., support_cutoff=...)` | You need a readable rule tree from discrete feature values. | Probabilities are not implemented for standard prediction. |
| `MaxentClassifier.train(train_toks, algorithm=None, trace=3, encoding=None, labels=None, gaussian_prior_sigma=0, **cutoffs)` | You need NLTK maximum entropy/log-linear classification. | Default algorithm is `IIS`; `GIS` and `IIS` use NLTK's implementation and require numeric support from `numpy`. `MEGAM` and `TADM` require configured external binaries. |
| `SklearnClassifier(estimator, dtype=float, sparse=True).train(train)` | You want an NLTK classifier interface over a scikit-learn estimator or pipeline. | Requires `scikit-learn`; prediction probabilities require the estimator to implement `predict_proba`. Set `sparse=False` for estimators that do not accept sparse matrices. |

MaxEnt training accepts cutoffs such as `max_iter`, `min_ll`, and `min_lldelta`. Set `trace=0` for non-verbose scripts.

## Clustering

`nltk.cluster` exposes vector-space clusterers:

| API | Contract | Notes |
| --- | --- | --- |
| `KMeansClusterer(num_means, distance, repeats=1, conv_test=1e-6, initial_means=None, normalise=False, svd_dimensions=None, rng=None, avoid_empty_clusters=False)` | K-means over numeric vectors. | Common distance helpers: `euclidean_distance`, `cosine_distance`. |
| `EMClusterer(initial_means, priors=None, covariance_matrices=None, conv_threshold=1e-6, bias=0.1, normalise=False, svd_dimensions=None)` | Gaussian mixture EM clustering. | Needs numeric arrays and enough data for covariance estimates. |
| `GAAClusterer(num_clusters=1, normalise=True, svd_dimensions=None)` | Group-average agglomerative clustering. | Provides dendrogram-style grouping. |
| `cluster(vectors, assign_clusters=True)` | Learn clusters and optionally return assignments. | `classify(vector)` assigns a new vector. |

Cluster workflows assume `numpy` arrays or array-like numeric vectors; many methods reference `numpy` even though imports are optional at module import time.

## Frequency and probability utilities

### Frequency distributions

| API | Contract |
| --- | --- |
| `FreqDist(samples=None)` | Counter-like mapping from sample to frequency count. Supports `update`, `most_common`, arithmetic (`+`, `-`, `|`, `&`), pickling, and count access. |
| `fd.N()` | Total sample outcomes recorded. |
| `fd.B()` / `len(fd)` | Number of bins with count > 0. |
| `fd.freq(sample)` | Relative frequency `fd[sample] / fd.N()`; returns `0` if `N()==0`. |
| `fd.hapaxes()` | Samples with count exactly 1. |
| `ConditionalFreqDist(cond_samples=None)` | Maps condition -> `FreqDist`; populate with `(condition, sample)` pairs or by indexing `cfd[condition][sample] += 1`. |

### Probability distributions

| API | Use |
| --- | --- |
| `MLEProbDist(fd)` | Maximum-likelihood probabilities from counts; unseen samples get zero probability. |
| `LidstoneProbDist(fd, gamma, bins=None)` | Add-`gamma` smoothing. |
| `LaplaceProbDist(fd, bins=None)` | Lidstone with `gamma=1`. |
| `ELEProbDist(fd, bins=None)` | Expected likelihood estimate; Lidstone with `gamma=0.5`. Naive Bayes default estimator. |
| `WittenBellProbDist(fd, bins=None)`, `KneserNeyProbDist(fd, bins=None, discount=0.75)` | Smoothing estimators for language/tagging-style distributions. |
| `DictionaryProbDist(prob_dict, log=False, normalize=False)` | Wrap explicit sample probabilities or log-probabilities. |
| `ConditionalProbDist(cfd, probdist_factory, *args, **kwargs)` | Convert each condition's `FreqDist` into a probability distribution with a shared factory. |

## N-gram language models

### Preprocessing and fitting

```python
from nltk.lm.preprocessing import padded_everygram_pipeline
from nltk.lm import Lidstone

sentences = [["a", "b", "a"], ["a", "c"]]
train_data, vocab_data = padded_everygram_pipeline(2, sentences)
lm = Lidstone(0.1, 2)
lm.fit(train_data, vocab_data)
```

Key contracts:

- `padded_everygram_pipeline(order, text)` returns two iterators:
  1. padded sentences converted to everygrams up to `order`;
  2. a flattened padded token stream for vocabulary construction.
- `text` is an iterable of tokenized sentences (`Iterable[Iterable[str]]`), not raw strings.
- The returned iterators are consumable; recreate them if you need to fit again.
- If an LM has no vocabulary and `fit(text, vocabulary_text=None)` is called without `vocabulary_text`, it raises `ValueError`.

### Models and scoring

| Model | Constructor | Behavior |
| --- | --- | --- |
| `MLE(order, vocabulary=None, counter=None)` | Maximum-likelihood counts. | Unseen n-grams can score `0`, which can make entropy/perplexity infinite. |
| `Lidstone(gamma, order, vocabulary=None, counter=None)` | Add-`gamma` smoothing. | Use small gamma values such as `0.1` or `0.2` for simple smoothed examples. |
| `Laplace(order, ...)` | Add-one smoothing. | Convenience `Lidstone(gamma=1)`. |
| `WittenBellInterpolated(order, **kwargs)` | Interpolated Witten-Bell. | Good general default, but based ultimately on sparse evidence; unseen test n-grams can still yield `inf` entropy in some setups. |
| `KneserNeyInterpolated(order, discount=0.1, **kwargs)` | Interpolated Kneser-Ney. | Discount must be between 0 and 1. |
| `AbsoluteDiscountingInterpolated(order, discount=0.75, **kwargs)` | Interpolated absolute discounting. | Backoff/interpolation model. |
| `StupidBackoff(alpha=0.4, order, ...)` | Backoff score. | Not a true probability distribution; scores for an order need not sum to 1. |

Common methods:

- `lm.score(word, context=None)` masks out-of-vocabulary words through `lm.vocab.lookup` before scoring.
- `lm.logscore(word, context=None)` is base-2 log score.
- `lm.context_counts(context)` returns counts for a context tuple.
- `lm.entropy(text_ngrams)` and `lm.perplexity(text_ngrams)` expect n-gram tuples, not raw sentences.
- `lm.generate(num_words=1, text_seed=None, random_seed=None)` can be deterministic with `random_seed`.

### Vocabulary and unseen words

`Vocabulary(counts=None, unk_cutoff=1, unk_label="<UNK>")` keeps counts and maps words below cutoff or absent from the vocabulary to `<UNK>`:

```python
from nltk.lm import Vocabulary
vocab = Vocabulary(["a", "a", "b"], unk_cutoff=2)
assert vocab.lookup("a") == "a"
assert vocab.lookup("b") == "<UNK>"
assert vocab.lookup("missing") == "<UNK>"
```

When interpreting LM results, always state the order, padding symbols (`<s>`, `</s>`), cutoff, unknown label, and smoothing model.

## Metrics

### IR-style and classifier scores

| API | Input | Edge behavior |
| --- | --- | --- |
| `nltk.metrics.accuracy(reference, test)` | Two same-length ordered lists. | Raises `ValueError` if lengths differ. |
| `precision(reference_set, test_set)` | Sets with `.intersection`. | Returns `None` if `test_set` is empty. |
| `recall(reference_set, test_set)` | Sets with `.intersection`. | Returns `None` if `reference_set` is empty. |
| `f_measure(reference_set, test_set, alpha=0.5)` | Sets. | Returns `None` if precision or recall is undefined; returns `0` if either is zero. |
| `ConfusionMatrix(reference, test, sort_by_count=False)` | Ordered sequences of gold/predicted labels. | Offers `pretty_format`, per-label `precision`, `recall`, and `f_measure`. |

### Distances, segmentation, agreement, association

- `edit_distance(s1, s2, substitution_cost=1, transpositions=False)` and `edit_distance_align` for string/sequence edit paths.
- `jaccard_distance`, `masi_distance`, `interval_distance`, `binary_distance` for label-set comparisons.
- `windowdiff(seg1, seg2, k, boundary="1", weighted=False)`, `pk`, and `ghd` for segmentation.
- `AnnotationTask` for inter-annotator agreement.
- `BigramAssocMeasures`, `TrigramAssocMeasures`, `QuadgramAssocMeasures`, and `ContingencyMeasures` for collocation/association scoring.

Some advanced statistical helpers use optional `scipy`; keep fallbacks explicit.

## Translation scores and alignment objects

### Translation metrics

| API | Input shape | Caveat |
| --- | --- | --- |
| `sentence_bleu(references, hypothesis, weights=..., smoothing_function=None, auto_reweigh=False)` | `references=[ref_tokens, ...]`, `hypothesis=hyp_tokens`. | Without smoothing, zero overlap at any higher order can drive sentence BLEU to `0`. Use `SmoothingFunction().method1` etc. |
| `corpus_bleu(list_of_references, hypotheses, ...)` | `[[ref_tokens, ...], ...]` and `[hyp_tokens, ...]`. | Corpus BLEU is micro-averaged; it is not the mean of sentence BLEU. |
| `sentence_gleu`, `corpus_gleu` | Tokenized references/hypotheses. | Min/max n-gram length parameters. |
| `sentence_chrf`, `corpus_chrf` | Strings or token sequences depending on caller preprocessing. | Character n-gram metric; `ignore_whitespace=True` by default. |
| `sentence_nist`, `corpus_nist` | Tokenized references/hypotheses. | Can fail when there is insufficient n-gram overlap. |
| `meteor_score`, `single_meteor_score` | Pre-tokenized iterables of strings. | Uses Porter stemming and WordNet synonyms by default; WordNet data may be required for synonym matching. |
| `sentence_ribes`, `sentence_lepor`, `corpus_lepor` | Tokenized references/hypotheses. | Useful for word-order-sensitive MT evaluation. |

### Alignment and aligned sentence contracts

```python
from nltk.translate import Alignment, AlignedSent

alignment = Alignment.fromstring("0-0 1-1")
sent = AlignedSent(["the", "house"], ["das", "Haus"], alignment)
assert sent.invert().alignment == alignment.invert()
```

- `Alignment` is a `frozenset` of `(i, j, ...)` pairs and prints in GIZA `i-j` form.
- `Alignment.fromstring("0-0 2-1")` parses zero-based `i-j` pairs.
- `alignment[i]` returns alignments from left index `i`; non-integer indices raise `TypeError`.
- `alignment.range(positions=None)` returns sorted right-side indices mapped from given left positions.
- `AlignedSent(words, mots, alignment=None)` stores target-side `words`, source-side `mots`, and an `Alignment` between them.
- Setting `AlignedSent.alignment` checks boundaries and raises `IndexError` if any index falls outside `words` or `mots`. A right index may be `None` for NULL alignments in IBM models.

`alignment_error_rate(reference, hypothesis, possible=None)` implements `1 - (|A∩S| + |A∩P|) / (|A| + |S|)`. With no separate possible alignment set, use sure/reference alignments as possible alignments.

### IBM Model 1 and phrase tables

```python
from nltk.translate import AlignedSent, IBMModel1

corpus = [
    AlignedSent(["the", "house"], ["das", "Haus"]),
    AlignedSent(["the", "book"], ["das", "Buch"]),
    AlignedSent(["a", "book"], ["ein", "Buch"]),
]
model = IBMModel1(corpus, 20)
prob = model.translation_table["book"]["Buch"]
```

- `IBMModel1(sentence_aligned_corpus, iterations, probability_tables=None)` trains immediately and mutates each `AlignedSent.alignment` with best alignments.
- The direction is from `AlignedSent.mots` (source) to `AlignedSent.words` (target); `translation_table[target_word][source_word]` stores probabilities.
- IBM Models 2-5 add fertility/distortion/alignment detail and are slower/more complex. Start with Model 1 for tiny examples.
- `PhraseTable` is exported from `nltk.translate` / `nltk.translate.api`, not from `nltk.translate.phrase_based`. Use `PhraseTable.add(src_phrase, trg_phrase, log_prob)` and `translations_for(src_phrase)` for stack-decoder-style phrase lookup.
