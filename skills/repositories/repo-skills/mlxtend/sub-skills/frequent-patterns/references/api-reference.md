# Frequent Patterns API Reference

Verified against the installed `mlxtend.frequent_patterns` and `mlxtend.preprocessing.TransactionEncoder` APIs, with source/tests confirming behavior.

## Public imports

```python
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, fpgrowth, fpmax, hmine, association_rules
```

## TransactionEncoder bridge

`TransactionEncoder()` converts list-of-lists transaction records into a boolean matrix suitable for a pandas one-hot DataFrame.

Verified methods:

| Method | Signature | Use |
|---|---|---|
| `fit` | `fit(X)` | Learn sorted unique item labels into `columns_` and an internal label-to-column map. |
| `transform` | `transform(X, sparse=False)` | Return a dense boolean NumPy array, or a CSR boolean matrix when `sparse=True`. |
| `fit_transform` | `fit_transform(X, sparse=False)` | Fit and transform in one step. |
| `inverse_transform` | `inverse_transform(array)` | Convert an encoded array back to transactions using `columns_`. |
| `get_feature_names_out` | `get_feature_names_out()` | Return the learned item labels for sklearn/pandas output integration. |
| `set_output` | `set_output(*, transform=None)` | sklearn transformer API; `transform="pandas"` can produce a pandas DataFrame directly in compatible sklearn versions. |

For deeper preprocessing, route to `../feature-workflows/SKILL.md`. For frequent-pattern mining, usually wrap the dense/sparse output as:

```python
te = TransactionEncoder()
encoded = te.fit_transform(transactions)
df = pd.DataFrame(encoded, columns=te.columns_)
```

## Itemset miners

All itemset miners expect a pandas DataFrame whose rows are transactions and whose columns are items. Values must be boolean or binary `0/1`; boolean dtype is preferred.

| Function | Verified signature | Output | Key notes |
|---|---|---|---|
| `apriori` | `apriori(df, min_support=0.5, use_colnames=False, max_len=None, verbose=0, low_memory=False, n_jobs=1)` | DataFrame with `support`, `itemsets` | Classic Apriori candidate generation. `low_memory=True` reduces peak candidate memory but is slower. `n_jobs` parallelizes default dense support counting; it is ignored by the low-memory branch and not useful for sparse support counting. |
| `fpgrowth` | `fpgrowth(df, min_support=0.5, null_values=False, use_colnames=False, max_len=None, verbose=0)` | DataFrame with `support`, `itemsets` | FP-tree miner for all frequent itemsets; usually preferable for larger/sparser baskets. Supports nullable input with `null_values=True`. |
| `fpmax` | `fpmax(df, min_support=0.5, null_values=False, use_colnames=False, max_len=None, verbose=0)` | DataFrame with `support`, `itemsets` | FP-Max miner that returns only maximal frequent itemsets. This is compact but does not include all subset supports needed by ordinary association-rule metrics. Supports nullable input with `null_values=True`. |
| `hmine` | `hmine(df, min_support=0.5, use_colnames=False, max_len=None, verbose=0) -> pandas.DataFrame` | DataFrame with `support`, `itemsets` | H-Mine frequent itemset miner; source/tests confirm parity with Apriori/FP-Growth on representative dense, bool, sparse, and empty cases. No `null_values`, `low_memory`, or `n_jobs` parameter. |

### Shared itemset parameters

- `df`: pandas one-hot DataFrame, dense or pandas sparse extension-backed DataFrame. Old pandas `SparseDataFrame` is not supported.
- `min_support`: fraction in `(0, 1]`; invalid values such as `0`, negative numbers, or `>1` raise `ValueError`.
- `use_colnames`: when `False`, `itemsets` contain integer column indices; when `True`, they contain the DataFrame column labels.
- `max_len`: optional maximum itemset length to mine. Use it to control combinatorial growth or request only singleton/pair/triple itemsets.
- `verbose`: prints progress/status. It changes console output only, not results.
- `null_values`: only `fpgrowth` and `fpmax`; set `True` when the one-hot DataFrame contains `NaN` as missing/unknown values.

### Itemset result schema

Every miner returns a pandas DataFrame with:

- `support`: float fraction in `[0, 1]` after applying the miner's support logic.
- `itemsets`: immutable `frozenset` objects, using labels when `use_colnames=True` or integer column indices otherwise.

An empty mining result is valid and still has columns `['support', 'itemsets']`.

## Association rules

Verified signature:

```python
association_rules(
    df: pandas.DataFrame,
    num_itemsets: Optional[int] = 1,
    df_orig: Optional[pandas.DataFrame] = None,
    null_values=False,
    metric="confidence",
    min_threshold=0.8,
    support_only=False,
    return_metrics: list = [
        "antecedent support", "consequent support", "support", "confidence",
        "lift", "representativity", "leverage", "conviction",
        "zhangs_metric", "jaccard", "certainty", "kulczynski",
    ],
) -> pandas.DataFrame
```

Required input columns in `df`:

- `support`
- `itemsets`

The `itemsets` entries may be sets/lists/frozensets, but mlxtend normalizes them internally to `frozenset` keys.

### Rule output columns

The returned DataFrame begins with:

- `antecedents`: `frozenset`
- `consequents`: `frozenset`

Then it includes the requested `return_metrics` columns. By default these are:

1. `antecedent support`
2. `consequent support`
3. `support`
4. `confidence`
5. `lift`
6. `representativity`
7. `leverage`
8. `conviction`
9. `zhangs_metric`
10. `jaccard`
11. `certainty`
12. `kulczynski`

If no rule passes `metric >= min_threshold`, the function returns an empty DataFrame with the same columns. If the input itemset DataFrame itself is empty, it raises `ValueError`.

### Rule metrics and filtering

`metric` selects the column used for thresholding. Source/tests confirm these metric names are accepted:

- `support`
- `confidence`
- `lift`
- `representativity`
- `leverage`
- `conviction`
- `zhangs_metric`
- `jaccard`
- `certainty`
- `kulczynski`

`min_threshold` is compared as `metric(rule) >= min_threshold`.

`support_only=True` forces metric selection to `support`, computes rule support, and fills all other requested metric columns with `NaN`. Use this when the itemset DataFrame is cropped and lacks antecedent/consequent subset supports; otherwise ordinary metrics may raise a `KeyError`.

### Null-aware rules

For association rules from nullable FP mining:

```python
frequent_itemsets = fpgrowth(df, min_support=0.6, null_values=True, use_colnames=True)
rules = association_rules(
    frequent_itemsets,
    num_itemsets=len(df),
    df_orig=df,
    null_values=True,
    metric="confidence",
    min_threshold=0.8,
)
```

When `null_values=True`, `association_rules` requires both `df_orig` and `num_itemsets`; omitting either raises `TypeError`.

## Algorithm choice summary

- Use `apriori` when you need classic Apriori behavior, want `low_memory=True`, or want to compare against textbook candidate generation.
- Use `fpgrowth` as the default all-frequent-itemset miner for many practical transaction datasets, especially sparse basket data.
- Use `fpmax` when maximal itemsets are the desired deliverable or itemset volume is too large, but switch to `apriori`/`fpgrowth`/`hmine` before full metric association rules.
- Use `hmine` as another all-frequent-itemset miner and a useful cross-check against Apriori/FP-Growth outputs.
