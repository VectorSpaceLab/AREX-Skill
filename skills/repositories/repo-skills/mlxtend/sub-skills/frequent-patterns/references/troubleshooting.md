# Frequent Patterns Troubleshooting

## Quick diagnosis table

| Symptom | Likely cause | Fix |
|---|---|---|
| `ValueError: min_support must be ... (0, 1]` | `min_support <= 0` or `min_support > 1` | Use a fractional threshold such as `0.01`, `0.1`, or `1.0` for items present in every transaction. |
| Warning about non-bool DataFrames | Input uses integer/object dtype | Prefer boolean one-hot data: `df = df.astype(bool)` when there are no `NaN` values. Binary `0/1` works but can warn about performance/future support. |
| `The allowed values for a DataFrame are True, False, 0, 1...` | Values other than bool/binary are present | Re-encode to one-hot; check accidental counts, strings, floats, or category labels in cells. |
| `NaN values are not permitted ... null_values=False` | Data contains missing values but miner is not null-aware | Use `fpgrowth(..., null_values=True)` or `fpmax(..., null_values=True)`, then pass `df_orig=df`, `num_itemsets=len(df)`, `null_values=True` to `association_rules`. |
| `SparseDataFrame support has been deprecated...` | Old pandas `SparseDataFrame` object | Use pandas sparse extension dtypes or `pd.DataFrame.sparse.from_spmatrix(...)`. |
| Sparse integer column-name error | Sparse DataFrame integer columns do not start at `0` | Use string item labels or integer columns starting at `0`. |
| Itemset result is empty | `min_support` too high, all-false/empty matrix, wrong orientation, or overly restrictive `max_len` | Inspect singleton supports with `df.mean(axis=0)`, lower `min_support`, check rows are transactions, and try `max_len=1`. |
| Rules result is empty | No itemsets of length ≥ 2 or `min_threshold` too high | Lower rule threshold, generate broad rules with `min_threshold=0.0`, and inspect metric distributions. |
| `association_rules` says input DataFrame is empty | Itemset mining returned no rows | Fix itemset thresholds/input before calling rule generation. |
| Missing `support`/`itemsets` column error | Input to `association_rules` is not a frequent itemsets DataFrame | Pass the raw output of `apriori`, `fpgrowth`, `hmine`, or appropriate `fpmax` output. |
| `KeyError` mentioning missing antecedent/consequent information | Cropped itemset table lacks subset supports | Generate rules from the full itemset table, or call `association_rules(..., support_only=True)`. |
| Wrong metric error | `metric` string not in mlxtend's metric dictionary | Use one of `support`, `confidence`, `lift`, `representativity`, `leverage`, `conviction`, `zhangs_metric`, `jaccard`, `certainty`, `kulczynski`. |
| Unexpected integer itemsets | `use_colnames=False` | Re-run mining with `use_colnames=True` or map indices to `df.columns`. |
| `fpmax` rules have missing metrics or fail | Maximal itemsets omit subset support | Use `fpgrowth`/`apriori`/`hmine` for full rule metrics; use `support_only=True` only when support-only output is enough. |
| Memory/runtime explosion | Low support on many items creates huge candidate/rule space | Increase `min_support`, set `max_len`, use `fpgrowth` or `hmine`, use sparse input, or use `apriori(low_memory=True)` if Apriori is required. |

## Input validation steps

Before mining, run checks like these:

```python
print(df.shape)
print(df.dtypes.value_counts())
print(df.head())
print(df.isna().any().any())
print(df.astype(float).mean(axis=0).sort_values(ascending=False).head(20))
```

Expected shape is `(n_transactions, n_items)`. If the shape looks reversed, transpose only after verifying that columns represent items and rows represent transactions.

## Nullable data pitfalls

- `apriori` and `hmine` do not expose a `null_values` parameter. They reject `NaN` under ordinary validation.
- `fpgrowth` and `fpmax` can handle `NaN` with `null_values=True`.
- For nullable rules, `association_rules` requires both `df_orig` and `num_itemsets`; source validation raises `TypeError` if either is omitted.
- Null-aware support and metrics use adjusted denominators. Do not compare them blindly with non-null runs unless the treatment of missing data is part of the analysis.
- If the DataFrame contains only booleans and no `NaN`, leave `null_values=False`.

## Empty itemset recovery workflow

1. Compute singleton supports:
   ```python
   supports = df.astype(float).mean(axis=0).sort_values(ascending=False)
   print(supports.head(30))
   ```
2. Choose `min_support` below at least a few singleton supports.
3. Try a constrained run:
   ```python
   itemsets = fpgrowth(df, min_support=0.1, max_len=2, use_colnames=True)
   ```
4. If still empty, verify that `True`/`1` means item presence and that the encoder did not create an all-false matrix.
5. If the input came from transactions, re-create it with `TransactionEncoder` and inspect `te.columns_` for unexpected tokenization/normalization issues.

## Empty rule recovery workflow

1. Ensure itemsets include combinations:
   ```python
   itemsets.assign(length=itemsets["itemsets"].map(len))["length"].value_counts()
   ```
2. Generate diagnostic rules at a low threshold:
   ```python
   rules0 = association_rules(itemsets, num_itemsets=len(df), metric="confidence", min_threshold=0.0)
   print(rules0[["support", "confidence", "lift"]].describe())
   ```
3. Pick thresholds from the observed range.
4. If `rules0` fails with missing subset support, re-mine full itemsets instead of passing filtered/maximal-only itemsets.

## Sparse and bool warnings

- Sparse pandas extension DataFrames are supported; raw SciPy sparse matrices are not the miner input type.
- For sparse DataFrames, string column names are the safest route.
- The miners accept binary integer data but prefer boolean. Future compatibility and speed are better with `bool` dtype.
- If you need nullable values, the dtype may become object/float; use null-aware FP mining rather than `astype(bool)`, which would destroy missingness.

## Parallelism and memory

- `apriori(n_jobs=...)` parallelizes only the default dense support-counting path. It does not make the low-memory generator branch faster.
- `n_jobs=-1` uses joblib's all-cores behavior, but mlxtend chunks candidates internally. Verify results against `n_jobs=1` if reproducibility is critical.
- `low_memory=True` is slower but reduces candidate matrix memory in Apriori.
- `fpgrowth` often scales better than Apriori for sparse transaction data, but low `min_support` can still produce too many itemsets.
- Rule generation can be large even when itemset mining succeeds. Filter itemsets by `max_len` during mining, or filter rules after generation based on support/confidence/lift.

## Frozenset handling

Itemsets and rule sides are `frozenset` objects. Correct selection examples:

```python
itemsets[itemsets["itemsets"] == frozenset(["Milk", "Bread"])]
rules[rules["consequents"] == frozenset(["Eggs"])]
```

Avoid comparing to display strings such as `"frozenset({'Milk', 'Bread'})"`. Plain Python `set` comparisons can work in pandas equality tests, but `frozenset` is the canonical stable form for dictionary keys, serialized checks, and explicit assertions.
