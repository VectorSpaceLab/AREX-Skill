# Labeling API Reference

## LF authoring

| API | Signature / defaults | Returns | Gotchas |
| --- | --- | --- | --- |
| `LabelingFunction` | `LabelingFunction(name, f, resources=None, pre=None)` | Callable LF object | `f` must return an `int`; `-1` means abstain. `pre` runs before `f`. `resources` are passed into `f` as keyword args. |
| `labeling_function` | `@labeling_function(name=None, resources=None, pre=None)` | `LabelingFunction` | Missing parentheses raises a `ValueError`. Name defaults to the wrapped function name. |
| LF preprocessors | `pre=[...]` on an LF | List of preprocessor callables | Each preprocessor must return a data point. Returning `None` raises `ValueError`. Keep complex mapper logic in the data-transforms sub-skill. |
| `SpacyPreprocessor` | `SpacyPreprocessor(text_field, doc_field, language='en_core_web_sm', disable=None, pre=None, memoize=False, memoize_key=None, gpu=False)` | Preprocessor object | This is the object inserted into NLP LFs. `NLPLabelingFunction` enables memoization by default. |

## Appliers

| API | Signature / defaults | Returns | Gotchas |
| --- | --- | --- | --- |
| `LFApplier` | `LFApplier(lfs)` then `apply(data_points, progress_bar=True, fault_tolerant=False, return_meta=False)` | `np.ndarray` or `(np.ndarray, ApplierMetadata)` | Accepts lists / sequences of data points or NumPy arrays. Set `fault_tolerant=True` to convert LF exceptions into `-1`. |
| `PandasLFApplier` | `PandasLFApplier(lfs)` then `apply(df, progress_bar=True, fault_tolerant=False, return_meta=False)` | `np.ndarray` or `(np.ndarray, ApplierMetadata)` | Works row-wise on a Pandas DataFrame. Faster than plain Python for small data, but still single-process. |
| `DaskLFApplier` | `DaskLFApplier(lfs)` then `apply(df, scheduler='processes', fault_tolerant=False)` | `np.ndarray` | Requires a Dask DataFrame. Scheduler may be a string or `Client`. Optional dependency: `dask[dataframe]` + `distributed`. |
| `PandasParallelLFApplier` | `PandasParallelLFApplier(lfs)` then `apply(df, n_parallel=2, scheduler='processes', fault_tolerant=False)` | `np.ndarray` | `n_parallel` must be `>= 2`. Use the plain Pandas applier for single-process runs. |
| `SparkLFApplier` | `SparkLFApplier(lfs)` then `apply(rdd, fault_tolerant=False)` | `np.ndarray` | Expects a Spark `RDD` of rows or records. Optional dependency: Java + PySpark. |
| `ApplierMetadata` | `ApplierMetadata(faults)` | Named tuple | `faults` maps LF name to the number of exceptions seen during a fault-tolerant apply call. |

### Common applier shape

- Input: `n` data points and `m` LFs.
- Output matrix: shape `[n, m]`.
- Abstain code: `-1`.
- Duplicate LF names are rejected before application.

## LFAnalysis

| API | Signature / defaults | Returns | Gotchas |
| --- | --- | --- | --- |
| `LFAnalysis` | `LFAnalysis(L, lfs=None)` | Analysis object | `L` must be an integer matrix of LF outputs. If `lfs` is provided, its length must match `L.shape[1]`. |
| `label_coverage()` | `()` | `float` | Fraction of rows with at least one non-abstain LF. |
| `label_overlap()` | `()` | `float` | Fraction of rows with at least two non-abstain LF outputs. |
| `label_conflict()` | `()` | `float` | Fraction of rows with conflicting LF outputs. |
| `lf_polarities()` | `()` | `list[list[int]]` | Returns the unique non-abstain labels each LF emitted. |
| `lf_coverages()` | `()` | `np.ndarray[m]` | Per-LF coverage fractions. |
| `lf_overlaps(normalize_by_coverage=False)` | `()` | `np.ndarray[m]` | If normalized, divide overlap by each LF's coverage. |
| `lf_conflicts(normalize_by_overlaps=False)` | `()` | `np.ndarray[m]` | If normalized, divide conflict by each LF's overlap fraction. |
| `lf_empirical_accuracies(Y)` | `(Y)` | `np.ndarray[m]` | Compare each LF against aligned gold labels. Gold labels should be `0..k-1`. |
| `lf_empirical_probs(Y, k)` | `(Y, k)` | `np.ndarray[m, k+1, k]` | Estimates `P(LF=l | Y=y)` for each LF. Use `k` equal to the class cardinality. |
| `lf_summary(Y=None, est_weights=None)` | `()` | `pandas.DataFrame` | Handy combined table. `est_weights` can be `LabelModel.get_weights()`. |

## LabelModel and voters

| API | Signature / defaults | Returns | Gotchas |
| --- | --- | --- | --- |
| `LabelModel` | `LabelModel(cardinality=2, **kwargs)` | Model object | Default config uses `verbose=True`, `device='cpu'`. Non-CPU device settings require CUDA availability. |
| `LabelModel.fit` | `fit(L_train, Y_dev=None, class_balance=None, progress_bar=True, **kwargs)` | `None` | Needs at least 3 LFs. `L_train` must use `-1` abstain and labels in `0..cardinality-1`. |
| `LabelModel.predict_proba` | `predict_proba(L)` | `np.ndarray[n, cardinality]` | Returns class probabilities. |
| `LabelModel.predict` | `predict(L, return_probs=False, tie_break_policy='abstain')` | `np.ndarray[n]` or `(preds, probs)` | Default tie-break is `abstain`, not random. Other policies: `random` and `true-random`. |
| `LabelModel.score` | `score(L, Y, metrics=['accuracy'], tie_break_policy='abstain')` | `dict[str, float]` | Uses Snorkel scoring utilities. `coverage` counts non-abstain predictions. `f1` is binary-only; use `f1_micro` or `f1_macro` for multiclass. `roc_auc` is binary-only. |
| `LabelModel.get_conditional_probs` | `()` | `np.ndarray[m, k+1, k]` | Returns learned LF conditional probabilities, including abstain rows. |
| `LabelModel.get_weights` | `()` | `np.ndarray[m]` | Derived LF weights for inspection and `LFAnalysis.lf_summary`. |
| `MajorityClassVoter` | `fit(balance)` then `predict_proba(L)` | `np.ndarray[n, k]` | Ignores `L` at prediction time and uses the stored class balance. |
| `MajorityLabelVoter` | `predict_proba(L)` | `np.ndarray[n, k]` | Majority vote across LFs. Ties can yield fractional probabilities. |
| `RandomVoter` | `predict_proba(L)` | `np.ndarray[n, k]` | Returns random normalized class probabilities row by row. |

### `LabelModel.fit` keyword defaults

Common `fit(..., **kwargs)` settings:

- `n_epochs=100`
- `lr=0.01`
- `l2=0.0`
- `optimizer='sgd'`
- `lr_scheduler='constant'`
- `prec_init=0.7`
- `seed=<random>`
- `log_freq=10`
- `mu_eps=None`

### `LabelModel.fit` class-balance rules

- `class_balance` wins when provided.
- If `class_balance` is omitted and `Y_dev` is provided, the class prior is estimated from `Y_dev`.
- If both are omitted, the prior is uniform.
- `class_balance` length must equal `cardinality` and must not contain zeros.

## Filtering unlabeled data

| API | Signature / defaults | Returns | Gotchas |
| --- | --- | --- | --- |
| `filter_unlabeled_dataframe` | `filter_unlabeled_dataframe(X, y, L)` | `(X_filtered, y_filtered)` | Keeps only rows where at least one LF labeled the example. `X` must be a Pandas DataFrame and `y` must align row-wise with `X` and `L`. |

## NLP and Spark helpers

| API | Signature / defaults | Returns | Gotchas |
| --- | --- | --- | --- |
| `NLPLabelingFunction` | `NLPLabelingFunction(name, f, resources=None, pre=None, text_field='text', doc_field='doc', language='en_core_web_sm', disable=None, memoize=True, memoize_key=None, gpu=False)` | LF object | Adds a shared spaCy preprocessor to the LF. The first instance fixes the NLP config for that LF class. Later instances with different params raise `ValueError`. |
| `nlp_labeling_function` | `@nlp_labeling_function(...)` | `NLPLabelingFunction` | Same missing-parentheses trap as the plain decorator. |
| `SparkNLPLabelingFunction` | `SparkNLPLabelingFunction(name, f, resources=None, pre=None, text_field='text', doc_field='doc', language='en_core_web_sm', disable=None, memoize=True, memoize_key=None, gpu=False)` | LF object | Spark-compatible spaCy LF helper. Uses the same LF contract, but the preprocessor is adapted for Spark execution. |
| `spark_nlp_labeling_function` | `@spark_nlp_labeling_function(...)` | `SparkNLPLabelingFunction` | Spark-only decorator helper. Optional dependency: Java + PySpark. |

### NLP helper notes

- Default spaCy model: `en_core_web_sm`.
- Default memoization for NLP LF helpers is `True`.
- Use `pre=[...]` for any small local preprocessing before spaCy parsing.
- For full preprocessing patterns, route to the data-transforms sub-skill.
