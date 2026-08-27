# Workflows: NLTK ML, Metrics, and Translation

Use these recipes as operating patterns. They avoid downloads and source-checkout dependencies unless they explicitly say a corpus/resource is required.

## 1. Build and inspect a small Naive Bayes classifier

Use when the user has labeled examples or wants a deterministic baseline classifier.

1. Convert raw objects to feature dictionaries.
2. Split into `train=[(featureset, label), ...]` and optional `test` in the same shape.
3. Train, predict, and score.
4. Inspect probabilities and informative features.

```python
from nltk.classify import NaiveBayesClassifier, accuracy

train = [
    ({"token:good": True, "has_exclaim": False}, "pos"),
    ({"token:great": True, "has_exclaim": True}, "pos"),
    ({"token:bad": True, "has_exclaim": False}, "neg"),
    ({"token:awful": True, "has_exclaim": True}, "neg"),
]
clf = NaiveBayesClassifier.train(train)
fs = {"token:good": True, "has_exclaim": True}
print(clf.classify(fs))
print(clf.prob_classify(fs).prob("pos"))
print(accuracy(clf, train))
print(clf.most_informative_features(5))
```

Checklist:

- Feature names should be stable strings; feature values should be booleans, strings, numbers, or other hashable values.
- Do not use `None` as a user-level feature value with Naive Bayes because it is reserved for implicit missing features.
- If a feature extractor is expensive or corpus-backed, wrap tokens with `apply_features(feature_func, tokens, labeled=True)` to build features lazily.

## 2. Choose MaxEnt or sklearn when Naive Bayes is not enough

Use MaxEnt for NLTK-native log-linear experiments and sklearn for modern estimators.

```python
from nltk.classify import MaxentClassifier

clf = MaxentClassifier.train(train, algorithm="IIS", trace=0, max_iter=50)
```

- Try `algorithm="IIS"` first for no external binary. `GIS` is also NLTK-native.
- `MEGAM` and `TADM` need external binary configuration and are not default/base workflows.
- If `numpy` is missing, NLTK-native MaxEnt training can fail even though `nltk.classify` imports.

For sklearn:

```python
from nltk.classify.scikitlearn import SklearnClassifier
from sklearn.naive_bayes import BernoulliNB

clf = SklearnClassifier(BernoulliNB()).train(train)
labels = clf.classify_many([fs for fs, _ in train])
```

- Requires `scikit-learn`.
- `prob_classify_many` requires `predict_proba` on the wrapped estimator.
- Set `sparse=False` when an estimator rejects sparse matrices.

## 3. Count observations and convert counts to probabilities

Use `FreqDist` when the user asks for frequencies, most common items, hapaxes, or simple probability estimates.

```python
from nltk.probability import FreqDist, ConditionalFreqDist, ELEProbDist, ConditionalProbDist

fd = FreqDist("abracadabra")
print(fd.N(), fd.B(), fd.most_common(3), fd.freq("a"))

pairs = [("vowel", ch) for ch in "abracadabra" if ch in "aeiou"]
cfd = ConditionalFreqDist(pairs)
cpd = ConditionalProbDist(cfd, ELEProbDist)
print(cpd["vowel"].prob("a"))
```

Rules of thumb:

- `FreqDist.freq(x)` is relative frequency, not a smoothed probability.
- Use `MLEProbDist` only when zero probability for unseen samples is acceptable.
- Use `ELEProbDist`, `LidstoneProbDist`, or `LaplaceProbDist` when the downstream algorithm must tolerate unseen samples.

## 4. Train a tiny n-gram LM with explicit padding and smoothing

Use this when a task asks for language-model probabilities, entropy, perplexity, or generation.

```python
from nltk.lm.preprocessing import padded_everygram_pipeline, padded_everygrams
from nltk.lm import Lidstone

sentences = [["a", "b", "a"], ["a", "c"]]
train_data, vocab_data = padded_everygram_pipeline(2, sentences)
lm = Lidstone(0.1, 2)
lm.fit(train_data, vocab_data)

print(lm.score("a", ("b",)))
print(lm.score("missing", ("b",)))       # looked up as <UNK>
print(lm.vocab.lookup("missing"))
print(lm.generate(3, random_seed=7))

eval_ngrams = list(padded_everygrams(2, ["a", "b", "a"]))
print(lm.entropy(eval_ngrams), lm.perplexity(eval_ngrams))
```

Interpretation checklist:

- State the order (`2` for bigram, `3` for trigram), padding symbols, smoothing model, and `Vocabulary` cutoff.
- Recreate `train_data` and `vocab_data` if they were iterated once already.
- If using `MLE` or sparse Witten-Bell setups, unseen n-grams can produce zero scores and infinite entropy/perplexity.
- `context` must be a tuple such as `("b",)`, not a string.

## 5. Compute precision, recall, F-measure, and confusion matrix

Use set metrics for predicted item sets and ordered accuracy/confusion for sequence labels.

```python
from nltk.metrics import precision, recall, f_measure, accuracy, ConfusionMatrix

reference = {"NP@0", "VP@2", "NP@4"}
predicted = {"NP@0", "NP@4", "PP@5"}
print(precision(reference, predicted))
print(recall(reference, predicted))
print(f_measure(reference, predicted))

ref_labels = ["N", "V", "N", "P"]
pred_labels = ["N", "N", "N", "P"]
print(accuracy(ref_labels, pred_labels))
print(ConfusionMatrix(ref_labels, pred_labels).pretty_format())
```

Edge cases:

- `precision(reference, set())` returns `None`.
- `recall(set(), test)` returns `None`.
- `f_measure` returns `None` when either side is empty, and `0` when precision or recall is zero.
- Ordered `accuracy` raises `ValueError` if list lengths differ.

## 6. Score translations safely

Use tokenized inputs. For sentence BLEU, add smoothing for short or low-overlap hypotheses.

```python
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from nltk.translate.gleu_score import sentence_gleu
from nltk.translate.chrf_score import sentence_chrf

refs = [["the", "cat", "sat"], ["a", "cat", "is", "sitting"]]
hyp = ["the", "cat", "is", "sitting"]
smooth = SmoothingFunction().method1
print(sentence_bleu(refs, hyp, smoothing_function=smooth))
print(sentence_gleu(refs, hyp))
print(sentence_chrf("the cat sat", "the cat is sitting"))
```

Metric caveats:

- Corpus BLEU is not the mean of sentence BLEU.
- METEOR expects pre-tokenized iterables in current NLTK and may need WordNet data for synonym matching.
- NIST can be undefined or fail with insufficient overlap; keep fallback metrics available.

## 7. Build and evaluate alignments

Use `Alignment` and `AlignedSent` for word-alignment tasks and AER checks.

```python
from nltk.translate import Alignment, AlignedSent, alignment_error_rate
from nltk.metrics import precision, recall

gold = Alignment.fromstring("0-0 1-1")
hyp = Alignment([(0, 0), (1, 0)])
pair = AlignedSent(["the", "house"], ["das", "Haus"], hyp)

print(pair.alignment)
print(pair.invert().alignment)
print(precision(gold, hyp), recall(gold, hyp))
print(alignment_error_rate(gold, hyp))
```

Boundary checklist:

- Indices are zero-based.
- For `AlignedSent(words, mots, alignment)`, the first index addresses `words`, the second addresses `mots`.
- Setting an out-of-range alignment raises `IndexError`.
- Non-integer alignment lookup keys raise `TypeError`.

## 8. Train IBM Model 1 on a tiny parallel corpus

Use this to demonstrate lexical translation without corpora or downloads.

```python
from nltk.translate import AlignedSent, IBMModel1

corpus = [
    AlignedSent(["the", "house"], ["das", "Haus"]),
    AlignedSent(["the", "book"], ["das", "Buch"]),
    AlignedSent(["a", "book"], ["ein", "Buch"]),
]
model = IBMModel1(corpus, 20)
print(round(model.translation_table["the"]["das"], 1))
print(round(model.translation_table["book"]["Buch"], 1))
print(corpus[0].alignment)
```

Important interpretation points:

- Direction is `mots` -> `words`; read probabilities as `translation_table[target_word][source_word]`.
- Model construction trains immediately and sets best alignments on the provided `AlignedSent` objects.
- IBM Models are iterative and can be slow on large corpora; start with a small sample and fixed iterations.

## 9. Smoke-check the installed runtime

From any working directory in an environment with NLTK installed:

```bash
python /path/to/skills/disco/nltk/sub-skills/ml-metrics-and-translation/scripts/ml_translate_smoke.py --json
```

Expected signal: exit code `0` plus deterministic classifier, LM, metric, and IBMModel1 summary values. The script performs no downloads.
