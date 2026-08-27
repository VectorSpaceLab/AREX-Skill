# Frequent Patterns Data Formats

## Raw transactions

The preferred raw form is a Python list of transactions, where each transaction is an iterable of item labels:

```python
transactions = [
    ["Milk", "Bread", "Eggs"],
    ["Milk", "Bread"],
    ["Bread", "Butter"],
]
```

`TransactionEncoder` learns sorted unique labels from `fit` and returns a boolean matrix from `transform`/`fit_transform`:

```python
from mlxtend.preprocessing import TransactionEncoder
import pandas as pd

te = TransactionEncoder()
encoded = te.fit_transform(transactions)
df = pd.DataFrame(encoded, columns=te.columns_)
```

Important format facts:

- `te.columns_` is sorted unique item labels.
- Dense `transform` returns a boolean NumPy array with shape `(n_transactions, n_unique_items)`.
- `transform(..., sparse=True)` returns a boolean SciPy CSR matrix; wrap it with `pd.DataFrame.sparse.from_spmatrix(..., columns=te.columns_)` for mining.
- Dense duplicate items in a transaction collapse naturally to `True`; sparse transformation uses a `set(transaction)` internally to avoid duplicate index problems.
- Unseen items at transform time are not silently ignored; fit on the desired vocabulary or filter/normalize transactions before encoding.
- For broader preprocessing decisions, read `../feature-workflows/SKILL.md`.

## One-hot pandas DataFrame schema

All itemset miners consume a pandas DataFrame:

| Axis | Meaning | Required properties |
|---|---|---|
| Rows | Transactions/baskets/events | Each row is one transaction. |
| Columns | Distinct items/features | Column labels become item labels when `use_colnames=True`. |
| Values | Item presence | Prefer boolean `True`/`False`; binary `0/1` also works but may warn about future performance/support. |

Example dense DataFrame:

```text
   Bread  Butter  Eggs   Milk
0   True   False  True   True
1   True   False False   True
2   True    True False  False
```

Constraints verified from source/tests:

- Allowed non-null values are `True`, `False`, `0`, and `1`.
- Non-bool dtypes can emit a deprecation/performance warning. Prefer `df = df.astype(bool)` when there are no `NaN` values.
- If `NaN` is present and `null_values=False`, input validation raises `ValueError`.
- Nullable `NaN` workflows are supported only by `fpgrowth(..., null_values=True)`, `fpmax(..., null_values=True)`, and matching `association_rules(..., null_values=True, df_orig=df, num_itemsets=len(df))`.
- Old pandas `SparseDataFrame` is not supported. Use pandas sparse extension dtypes/DataFrames.
- For sparse DataFrames with integer column labels, tests confirm labels starting at `0` are accepted; integer labels starting elsewhere can raise a pandas-limitation `ValueError`. String labels avoid the issue.

## Sparse one-hot DataFrames

Use sparse data when the transaction matrix is mostly `False`/`0`:

```python
te = TransactionEncoder()
csr = te.fit_transform(transactions, sparse=True)
df_sparse = pd.DataFrame.sparse.from_spmatrix(csr, columns=te.columns_)
```

Sparse DataFrames are accepted by `apriori`, `fpgrowth`, `fpmax`, and `hmine`. Keep the DataFrame interface; do not pass raw CSR matrices directly to the miners.

## Frequent itemset output schema

All miners return a DataFrame with exactly these core columns:

| Column | Type | Meaning |
|---|---|---|
| `support` | float | Fraction of transactions satisfying the itemset, after any null-aware denominator logic. |
| `itemsets` | `frozenset` | Immutable set of item identifiers. Uses labels if `use_colnames=True`; otherwise integer column positions. |

Example:

```text
   support                 itemsets
0     0.75                  (Bread)
1     0.50             (Bread, Milk)
2     0.50       (Bread, Eggs, Milk)
```

In pandas display, `frozenset({'Bread', 'Milk'})` may render compactly; compare values with `frozenset({...})`, not strings.

### `use_colnames` impact

```python
apriori(df, min_support=0.5, use_colnames=False)["itemsets"]  # frozenset({0, 3})
apriori(df, min_support=0.5, use_colnames=True)["itemsets"]   # frozenset({'Bread', 'Milk'})
```

Choose `use_colnames=True` for human-readable rules. Choose `False` only when integer column positions are easier to map downstream.

### Empty itemsets

An empty mining result is valid:

```text
Columns: [support, itemsets]
Index: []
```

This usually means `min_support` is above the observed support of every candidate itemset, the one-hot matrix is empty/all-false, or filtering with `max_len`/preprocessing removed usable items.

## Association rule input schema

`association_rules` expects a frequent-itemsets DataFrame containing:

- `support`
- `itemsets`

For ordinary metrics such as confidence/lift/leverage, the itemsets table must include support for the combined itemset and all antecedent/consequent subsets required by candidate rules. Outputs from `apriori`, `fpgrowth`, and `hmine` are appropriate. `fpmax` returns only maximal itemsets, so use it for maximal-itemset analysis or call `association_rules(..., support_only=True)` if support-only rules are acceptable.

## Association rule output schema

Rule output begins with:

| Column | Type | Meaning |
|---|---|---|
| `antecedents` | `frozenset` | Left-hand side itemset `A`. |
| `consequents` | `frozenset` | Right-hand side itemset `C`. |

Default metric columns then follow:

| Column | Meaning |
|---|---|
| `antecedent support` | Support of `A`. |
| `consequent support` | Support of `C`. |
| `support` | Support of `A ∪ C`. |
| `confidence` | Probability of `C` given `A`. |
| `lift` | Ratio of observed co-occurrence to independence expectation. |
| `representativity` | Null-aware information-availability metric; equals complete representation in non-null ordinary data. |
| `leverage` | Difference between observed support and independent expectation. |
| `conviction` | Directional implication-strength metric; can be infinite when confidence is 1. |
| `zhangs_metric` | Normalized association measure in `[-1, 1]`. |
| `jaccard` | Intersection over union for antecedent/consequent occurrence. |
| `certainty` | Certainty factor derived from confidence and consequent support. |
| `kulczynski` | Average of directional confidences. |

With `support_only=True`, all metric columns except `support` are present but filled with `NaN`.
