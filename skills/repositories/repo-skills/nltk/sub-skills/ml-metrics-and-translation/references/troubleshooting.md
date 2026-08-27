# Troubleshooting: NLTK ML, Metrics, and Translation

Use this when a workflow fails after routing to this sub-skill. Prefer tiny no-download repros before adding corpora, optional packages, or external binaries.

## Import and optional dependency failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'numpy'` during clustering or MaxEnt training | Some NLTK modules import without `numpy`, but vector operations and MaxEnt internals use it. | Install `numpy` in the active environment or choose a pure classifier such as Naive Bayes. |
| `ModuleNotFoundError: No module named 'sklearn'` for `SklearnClassifier` | `scikit-learn` is optional. | Install `scikit-learn` or use `NaiveBayesClassifier`, `DecisionTreeClassifier`, or NLTK MaxEnt. |
| `LookupError` / `NameError` mentioning MEGAM or TADM | `MaxentClassifier.train(..., algorithm='MEGAM'/'TADM')` needs external binaries. | Use `algorithm='IIS'`/`'GIS'`, or configure the binary with `nltk.config_megam(...)` / `nltk.classify.tadm.config_tadm(...)`. |
| Wrapped sklearn estimator errors on sparse input | `SklearnClassifier` defaults to `sparse=True`. | Construct `SklearnClassifier(estimator, sparse=False)` or use an estimator/pipeline that accepts sparse matrices. |
| `prob_classify_many` fails on sklearn wrapper | Estimator lacks `predict_proba`. | Use an estimator with probabilities, calibrate it, or call `classify_many` only. |
| METEOR raises a WordNet `LookupError` | Default METEOR synonym matching touches WordNet. | Install the targeted WordNet data via the data/downloader guidance, or use exact/stem-only logic/another metric. |

Optional external wrappers and binaries (Weka, MEGAM, TADM, Graphviz for SVG alignment display, Java/server-backed tools) are not required for the minimum base workflows. Do not install broad extras unless the task needs them.

## Classifier feature and training issues

| Symptom | Cause | Fix |
| --- | --- | --- |
| Classifier training sees raw strings or token lists as features | Training data was not converted to `[(featureset_dict, label), ...]`. | Write a feature extractor that returns a `dict`; then map every labeled token/document to `(featureset, label)`. |
| `ValueError`, `TypeError`, or odd predictions from feature values | Feature values are unstable/mutable, too sparse, or inconsistent across train/test. | Use stable booleans, strings, numbers, and consistent feature names. Avoid lists/dicts as values. |
| Naive Bayes result ignores a feature | The feature name was never seen during training. | Ensure the feature extractor emits the same feature names during training and prediction. |
| Naive Bayes predictions are distorted by `None` | `None` is reserved internally for missing feature values. | Use an explicit string/sentinel such as `'<MISSING>'` for user-level missing data. |
| `DecisionTreeClassifier.prob_classify` raises `NotImplementedError` | Decision-tree probabilities are not implemented. | Use `classify`/`classify_many`, or choose Naive Bayes/MaxEnt/sklearn estimator with probabilities. |
| `MaxentClassifier.train` is too verbose or slow | Default `trace=3`; too many iterations/features. | Set `trace=0`, lower `max_iter`, add feature cutoffs, or start with Naive Bayes. |

## Clustering issues

| Symptom | Cause | Fix |
| --- | --- | --- |
| Vector arithmetic errors | Vectors are Python lists or mixed types where numeric arrays are expected. | Convert to `numpy.array` with consistent numeric dimensions. |
| `KMeansClusterer` returns unstable assignments | Random initialization or insufficient repeats. | Pass deterministic `rng`, explicit `initial_means`, or increase `repeats`. |
| Cosine/euclidean distance fails | Zero vectors or missing `numpy`. | Remove/guard zero vectors and install `numpy`. |
| EM clustering fails with covariance errors | Too little data or degenerate covariance. | Provide more examples, better initial means, or use k-means for a small baseline. |

## Frequency and probability issues

| Symptom | Cause | Fix |
| --- | --- | --- |
| `FreqDist.freq(x)` returns `0` for everything | Empty frequency distribution (`fd.N()==0`). | Verify samples were passed or `fd.update(samples)` was called. |
| Unseen events get zero probability | `MLEProbDist` has no smoothing. | Use `ELEProbDist`, `LidstoneProbDist`, `LaplaceProbDist`, or another smoothed estimator. |
| Conditional probability missing condition | `ConditionalFreqDist` has no samples under that condition. | Check `cfd.conditions()` and populate `cfd[condition]` before wrapping with `ConditionalProbDist`. |
| Probability sums are unexpected | Wrong `bins`, wrong smoothing factory, or mixed samples/conditions. | State bins explicitly for smoothed distributions and inspect `fd.N()`, `fd.B()`, and `samples()`. |

## Language-model failures

| Symptom | Cause | Fix |
| --- | --- | --- |
| `ValueError: Cannot fit without a vocabulary or text to create it from.` | `fit` was called without `vocabulary_text` on an empty-vocabulary model. | Use `padded_everygram_pipeline(order, tokenized_sentences)` and pass both iterators to `fit`. |
| Model scores every unknown as `<UNK>` | Vocabulary cutoff excludes low-frequency words. | Inspect `lm.vocab.cutoff`, `lm.vocab.lookup(word)`, and token counts. Lower cutoff or provide more training text. |
| Entropy/perplexity is `inf` | Evaluation n-grams receive zero score, often with sparse/MLE-like evidence. | Add smoothing (`Lidstone`, `Laplace`, interpolated models), include `<UNK>` evidence, or filter/diagnose unseen n-grams. |
| `score(word, context)` gives surprising result | `context` was passed as a string, too long, or unpadded. | Pass a tuple like `('previous',)`, let the model truncate to order-1, and make padding explicit. |
| Second `fit` or debug print sees empty training data | `padded_everygram_pipeline` returns iterators that were already consumed. | Recreate `train_data, vocab_data` each time. |
| `generate` is nondeterministic | No random seed. | Pass `random_seed=<int>` for reproducible examples. |

## Metrics edge cases

| Symptom | Cause | Fix |
| --- | --- | --- |
| `precision` returns `None` | Test/predicted set is empty. | Handle undefined precision explicitly; do not format as a float without checking. |
| `recall` returns `None` | Reference/gold set is empty. | Handle undefined recall explicitly. |
| `f_measure` returns `None` or `0` | Undefined precision/recall or no overlap. | Check set sizes and intersection before reporting. |
| `accuracy` raises `ValueError` | Reference and test lists differ in length. | Align prediction and reference sequences before scoring. |
| `ConfusionMatrix` rows/columns look odd | Inputs are strings, so characters are treated as labels. | Pass token/label lists if character-level evaluation is not intended. |
| Segmentation metric values are unexpected | Boundary strings differ in length or boundary symbol. | Verify `seg1`, `seg2`, `k`, and `boundary='1'` semantics. |

## Translation score issues

| Symptom | Cause | Fix |
| --- | --- | --- |
| Sentence BLEU is `0` for a plausible short translation | Higher-order n-gram precision is zero. | Use `SmoothingFunction().method1` or lower-order/custom weights for sentence-level diagnostics. |
| Corpus BLEU disagrees with average sentence BLEU | Corpus BLEU micro-averages counts across the corpus. | Report both only if you explain the difference. |
| BLEU/GLEU/NIST inputs fail or score oddly | Inputs are raw strings instead of token lists. | Tokenize first and pass `references=[ref_tokens]`, `hypothesis=hyp_tokens`. |
| CHRF result differs after whitespace changes | `ignore_whitespace=True` by default. | Set `ignore_whitespace=False` if whitespace should matter. |
| METEOR raises type errors | Current NLTK expects pre-tokenized iterables, not raw sentence strings. | Pass `['token', ...]` lists for references and hypothesis. |
| NIST raises an error on tiny examples | Not enough informative n-gram overlap. | Fall back to BLEU/GLEU/CHRF or use a larger evaluation set. |

## Alignment and IBM-model issues

| Symptom | Cause | Fix |
| --- | --- | --- |
| `IndexError: Alignment is outside boundary of words/mots` | Alignment pair index is out of range for `AlignedSent(words, mots, alignment)`. | Remember first index addresses `words`; second index addresses `mots`; both are zero-based. |
| Alignment lookup with slices fails | `Alignment.__getitem__` only accepts integer left indices. | Use `alignment.range(...)`, set operations, or integer lookup. |
| AER result seems inverted | Arguments or possible/sure sets are swapped. | Use `alignment_error_rate(reference_sure, hypothesis, possible=reference_possible)`; with no possible set, sure is reused as possible. |
| IBM Model 1 translation table direction is confusing | Training direction is `mots` -> `words`. | Read `translation_table[target_word][source_word]`; `AlignedSent.words` are target-side words and `mots` are source-side words. |
| IBM training changes input objects | IBM model constructors call `align_all` and set `AlignedSent.alignment`. | Copy or recreate the corpus if the original unaligned examples must be preserved. |
| IBM training is slow | Iterative EM on large corpora. | Start with a sampled corpus and fixed iterations; use Model 1 before higher IBM models. |
| `PhraseTable` import from `nltk.translate.phrase_based` fails | `PhraseTable` lives in `nltk.translate.api` and is exported from `nltk.translate`. | `from nltk.translate import PhraseTable` or `from nltk.translate.api import PhraseTable`. |

## No-download smoke check

Run the bundled script from any working directory in an environment with NLTK installed:

```bash
python /path/to/ml_translate_smoke.py --help
python /path/to/ml_translate_smoke.py --json
```

If the smoke fails, treat the failure as an environment/import issue first because the script uses only tiny in-memory examples and performs no NLTK data downloads.
