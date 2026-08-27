# Workflows

## 1) Build a shared mapper / preprocessor chain

Use this when you want a reusable copy-safe transform that can feed later LF or SF logic.

```python
from types import SimpleNamespace
from snorkel.preprocess import preprocessor

@preprocessor()
def normalize_text(x):
    x.text = x.text.strip().lower()
    return x

@preprocessor(pre=[normalize_text], memoize=True)
def add_text_len(x):
    x.text_len = len(x.text)
    return x

sample = SimpleNamespace(text="  Jane plays soccer.  ")
result = add_text_len(sample)
```

What to expect:

- `sample` stays unchanged.
- The normalizer runs before the feature builder.
- Repeated calls with the same input reuse the cached output.

If the next step is weak supervision, hand the shared preprocessor to the sibling labeling skill through `pre=[...]`. If the next step is slice logic, hand it to the sibling slicing skill through `pre=[...]`.

## 2) Add spaCy parsing as a shared preprocessor

Use this when a text workflow needs a parsed `Doc` field.

```python
from snorkel.preprocess.nlp import SpacyPreprocessor

spacy_pre = SpacyPreprocessor(
    text_field="text",
    doc_field="doc",
    memoize=True,
)
```

Guidance:

- Keep the `text_field` and `doc_field` names explicit so downstream code is easy to read.
- Reuse the same preprocessor object anywhere you want the same cache.
- `gpu=True` only requests GPU preference; it does not replace model installation.

For later LF or SF work, use the parsed `doc` in the sibling skill rather than rebuilding the parser there.

## 3) Adapt a mapper or preprocessor for Spark `Row`

Use this when the input is a Spark row instead of a mutable Python object.

```python
from pyspark.sql import Row
from snorkel.map import Mapper
from snorkel.map.spark import make_spark_mapper
from snorkel.preprocess import Preprocessor
from snorkel.preprocess.spark import make_spark_preprocessor

class AddLength(Mapper):
    def run(self, text: str):
        return dict(text_len=len(text))

class AddTextNorm(Preprocessor):
    def run(self, text: str):
        return dict(text_norm=text.strip().lower())

mapper = make_spark_mapper(AddLength("add_length"))
spark_preprocessor = make_spark_preprocessor(AddTextNorm("add_text_norm"))

row = Row(text="  Abc  ")
mapped = mapper(row)
normalized = spark_preprocessor(row)
```

What to remember:

- `Row` is immutable, so the wrappers rebuild the row from field dicts.
- The wrapper patches the mapper object in place.
- This is a local compatibility step; you still need a working Spark environment if you intend to execute real Spark jobs.
- Apply the wrapped object to a `Row` just as you would any other mapper-style object.

## 4) Choose an augmentation policy

Use the policy that matches how you want TF sequences generated.

- `ApplyOnePolicy`: one TF only, useful for a single transform or a quick baseline.
- `ApplyEachPolicy`: one transformed copy per TF, useful for debugging and ablations.
- `ApplyAllPolicy`: run every TF in a fixed order.
- `MeanFieldPolicy`: sample TF indices from a distribution when you have weights.
- `RandomPolicy`: uniform sampling baseline.

Example for a safe `None`-aware augmentation run:

```python
from types import SimpleNamespace
import pandas as pd
from snorkel.augmentation import ApplyOnePolicy, PandasTFApplier, TFApplier, transformation_function

@transformation_function()
def add_ten_or_drop(x):
    if x.num == 2:
        return None
    x.num += 10
    return x

policy = ApplyOnePolicy(n_per_original=1, keep_original=True)
records = [SimpleNamespace(num=1), SimpleNamespace(num=2)]
augmented_records = TFApplier([add_ten_or_drop], policy).apply(records, progress_bar=False)

frame = pd.DataFrame({"num": [1, 2]})
augmented_frame = PandasTFApplier([add_ten_or_drop], policy).apply(frame, progress_bar=False)
```

Why this pattern works:

- The original examples stay intact because the appliers work on copies.
- `keep_original=True` keeps the unmodified input even when the TF returns `None`.
- The Pandas result keeps the source row index, so repeated indices are expected.

## 5) Generate synthetic label matrices

Use this when you need a tiny, reproducible label-model fixture.

```python
import numpy as np
from snorkel.synthetic.synthetic_data import generate_simple_label_matrix

np.random.seed(7)
P, Y, L = generate_simple_label_matrix(n=5, m=3, cardinality=2, abstain_multiplier=1.25)
```

Recommended follow-up checks:

- `P.shape == (3, 3, 2)` for this example.
- `Y.shape == (5,)`.
- `L.shape == (5, 3)` and abstains appear as `-1`.
- Column sums of `P` should equal 1 after normalization.

The returned `L` is a compact synthetic weak-label fixture, so the next step is usually the sibling labeling skill.
