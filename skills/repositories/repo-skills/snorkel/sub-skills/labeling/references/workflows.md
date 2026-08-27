# Labeling Workflows

## 1) Author LFs with local preprocessors and resources

Use `resources` for small constants and `pre=[...]` for light local preprocessing that belongs to the LF.

```python
import pandas as pd
from snorkel.labeling import PandasLFApplier, labeling_function, LFAnalysis
from snorkel.preprocess import preprocessor

@preprocessor()
def add_len(x):
    x.n_tokens = len(str(x.text).split())
    return x

@labeling_function(resources={"keyword": "cat"})
def has_cat(x, keyword):
    return 1 if keyword in x.text.lower() else -1

@labeling_function(pre=[add_len])
def is_short(x):
    return 0 if x.n_tokens <= 1 else -1

@labeling_function()
def mentions_dog(x):
    return 1 if "dog" in x.text.lower() else -1
```

Keep the LF logic small and readable. If you need a reusable mapper or more complex preprocessing stack, move that work to the data-transforms sub-skill.

## 2) Apply LFs to a Pandas DataFrame, list, or NumPy array

```python
df = pd.DataFrame({"text": ["cat", "small dog", "other", "cat dog", "plain words"]})
applier = PandasLFApplier([has_cat, is_short, mentions_dog])
L, meta = applier.apply(df, progress_bar=False, fault_tolerant=True, return_meta=True)

print(L.shape)           # [n_examples, n_lfs]
print(dict(meta.faults))  # empty when nothing failed
```

Other input shapes:

- `LFApplier` for lists / sequences of data points or NumPy arrays
- `DaskLFApplier` for Dask DataFrames
- `SparkLFApplier` for Spark RDDs

## 3) Inspect the label matrix before training

Always inspect the matrix before fitting a label model.

```python
analysis = LFAnalysis(L, [has_cat, is_short, mentions_dog])
print("coverage", analysis.label_coverage())
print("overlap", analysis.label_overlap())
print("conflict", analysis.label_conflict())
print(analysis.lf_summary())
```

What to look for:

- very low coverage: the LFs are abstaining too often
- high conflict: LFs may disagree on polarity or target definition
- a never-firing LF: the polarity list will be empty
- wrong cardinality: label values should be `-1` or `0..k-1`

If the matrix is all abstain or nearly all abstain, fix the LFs before touching `LabelModel`.

## 4) Train a LabelModel and inspect probabilities

`LabelModel` needs at least 3 LFs.

```python
from snorkel.labeling.model import LabelModel

label_model = LabelModel(cardinality=2, verbose=False)
label_model.fit(L, n_epochs=25, lr=0.01, seed=123, progress_bar=False)

probs = label_model.predict_proba(L)
preds = label_model.predict(L)
weights = label_model.get_weights()
print(probs.shape, preds.shape, weights.shape)
```

Helpful debugging order:

1. check the label matrix with `LFAnalysis`
2. check `label_model.get_conditional_probs()`
3. compare against a voter baseline
4. lower the learning rate if training becomes unstable

For baselines:

```python
from snorkel.labeling.model import MajorityLabelVoter

mv = MajorityLabelVoter()
probs = mv.predict_proba(L)
```

## 5) Turn weak labels into downstream training data

`LabelModel.predict_proba` gives probabilistic labels. Before training a discriminative model, drop rows with no LF coverage.

```python
from snorkel.labeling import filter_unlabeled_dataframe

X_train, probs_train = filter_unlabeled_dataframe(df, probs, L)
```

Typical handoff:

- `L` from LF application
- `LFAnalysis` to debug the matrix
- `LabelModel` or a voter to create weak labels
- `filter_unlabeled_dataframe` to keep only covered rows
- pass the filtered rows and probabilities to the classification sub-skill

## 6) Dask, Spark, and NLP migration notes

### Dask

Assume the LF definitions and Pandas fixture above.

```python
import dask.dataframe as dd
from snorkel.labeling.apply.dask import DaskLFApplier, PandasParallelLFApplier

ddf = dd.from_pandas(df, npartitions=2)
L = DaskLFApplier([has_cat, is_short, mentions_dog]).apply(ddf)

# Parallel Pandas DataFrame
L = PandasParallelLFApplier([has_cat, is_short, mentions_dog]).apply(df, n_parallel=4)
```

Notes:

- `PandasParallelLFApplier` requires `n_parallel >= 2`
- if process-based scheduling is flaky, try `scheduler="threads"` or a Dask `Client`
- keep the data point objects simple and serializable

### Spark

Assume the LF definitions and Pandas fixture above.

```python
from pyspark.sql import SparkSession
from snorkel.labeling.apply.spark import SparkLFApplier

spark = SparkSession.builder.master("local[1]").getOrCreate()
rdd = spark.createDataFrame(df).rdd
L = SparkLFApplier([has_cat, is_short, mentions_dog]).apply(rdd)
```

Notes:

- local Spark requires Java and PySpark
- set `SPARK_LOCAL_HOSTNAME=localhost` if local hostname resolution fails
- keep the smoke fixture tiny and in-memory

### NLP helpers

Use the NLP decorators when the LF logic depends on spaCy `Doc` objects.

- `NLPLabelingFunction` for local execution
- `spark_nlp_labeling_function` for Spark execution

Defaults to remember:

- text field: `text`
- parsed doc field: `doc`
- spaCy model: `en_core_web_sm`
- memoization: enabled for NLP LF helpers

## 7) Quick sanity baseline when the label model looks wrong

When you are unsure whether the LF matrix or the model is the problem, compare against a voter:

```python
from snorkel.labeling.model import MajorityLabelVoter, RandomVoter

mv = MajorityLabelVoter()
rv = RandomVoter()
print(mv.predict_proba(L))
print(rv.predict_proba(L))
```

If the voter looks reasonable but `LabelModel` does not, re-check the matrix polarity, cardinality, and class-balance assumptions.
