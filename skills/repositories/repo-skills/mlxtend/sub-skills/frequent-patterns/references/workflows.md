# Frequent Patterns Workflows

## 1. Transaction list to association rules

Use this when the source data is a list of baskets/transactions.

```python
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth, association_rules

transactions = [
    ["Milk", "Bread", "Eggs"],
    ["Milk", "Bread"],
    ["Milk", "Eggs"],
    ["Bread", "Eggs"],
    ["Milk", "Bread", "Eggs"],
]

te = TransactionEncoder()
onehot = te.fit_transform(transactions)
df = pd.DataFrame(onehot, columns=te.columns_)

itemsets = fpgrowth(df, min_support=0.4, use_colnames=True)
rules = association_rules(
    itemsets,
    num_itemsets=len(df),
    metric="confidence",
    min_threshold=0.7,
)
```

Checklist:

1. Confirm `df.shape[0] == len(transactions)` and `df.dtypes` are boolean.
2. Start with `use_colnames=True` unless downstream code explicitly wants integer column indices.
3. Mine itemsets with a support threshold low enough to include singletons and candidate combinations.
4. Generate rules only after itemsets include subset supports; prefer `apriori`, `fpgrowth`, or `hmine` output for ordinary metrics.
5. Filter/sort rules explicitly, for example `rules.sort_values(["lift", "confidence"], ascending=False)`.

## 2. Choosing the mining algorithm

| Situation | Recommended route |
|---|---|
| Need a default practical all-frequent-itemset miner | `fpgrowth(df, min_support=..., use_colnames=True)` |
| Need textbook Apriori behavior or candidate-generation comparison | `apriori(df, min_support=..., use_colnames=True)` |
| Need to reduce Apriori peak memory | `apriori(..., low_memory=True)`; expect slower runtime. |
| Need parallel dense Apriori support counting | `apriori(..., n_jobs=-1)` or a positive worker count; compare against `n_jobs=1` for reproducibility. |
| Need only maximal itemsets | `fpmax(...)`; do not expect a complete subset lattice. |
| Need another all-itemset cross-check | `hmine(...)` and compare sorted `itemsets`/`support`. |
| Input has `NaN` missing/unknown values | Use `fpgrowth(..., null_values=True)` or `fpmax(..., null_values=True)`; `apriori` and `hmine` do not expose null-aware mode. |
| Rule metrics are the deliverable | Mine all frequent itemsets (`apriori`, `fpgrowth`, or `hmine`) before `association_rules`. |

## 3. Filtering itemsets before rules

Itemset outputs are ordinary pandas DataFrames. It is safe to add temporary analysis columns outside persisted datasets:

```python
itemsets = fpgrowth(df, min_support=0.3, use_colnames=True)
itemsets = itemsets.assign(length=itemsets["itemsets"].map(len))

pairs = itemsets[itemsets["length"] == 2]
strong = itemsets[itemsets["support"] >= 0.5]
```

Do not pass a cropped itemset table to `association_rules` unless either:

- it still contains every antecedent and consequent subset needed for the candidate rules, or
- you intentionally call `association_rules(..., support_only=True)`.

A common safe pattern is: generate rules from the full itemsets table, then filter the rules DataFrame.

## 4. Rule filtering patterns

Generate broad enough rules, then sort/filter by business objective:

```python
rules = association_rules(
    itemsets,
    num_itemsets=len(df),
    metric="confidence",
    min_threshold=0.6,
)

# Higher-than-chance co-occurrence and good directionality.
interesting = rules[
    (rules["lift"] >= 1.2)
    & (rules["confidence"] >= 0.7)
    & (rules["support"] >= 0.2)
].sort_values(["lift", "confidence", "support"], ascending=False)
```

Metric guidance:

- Use `support` to keep rules that affect enough transactions.
- Use `confidence` for directional reliability: when antecedent appears, consequent appears often.
- Use `lift` to require more co-occurrence than expected under independence.
- Use `leverage` to measure absolute support gain over independence.
- Use `conviction`, `certainty`, `zhangs_metric`, `jaccard`, or `kulczynski` when the task explicitly requests these association measures or when confidence/lift alone are misleading.
- Use `representativity` primarily with nullable mining, where missing information matters.

## 5. Null-aware mining and rules

Only `fpgrowth` and `fpmax` expose `null_values=True` for `NaN`-containing one-hot data.

```python
itemsets = fpgrowth(df_with_nan, min_support=0.4, null_values=True, use_colnames=True)
rules = association_rules(
    itemsets,
    num_itemsets=len(df_with_nan),
    df_orig=df_with_nan,
    null_values=True,
    metric="confidence",
    min_threshold=0.7,
)
```

Rules for nullable data require both the original DataFrame and the original number of transactions. The metrics adjust denominators based on disabled/missing values; do not mix null-aware itemsets with a non-null-aware `association_rules` call.

If there are no `NaN` values, prefer `null_values=False` for simpler and faster output.

## 6. Sparse data workflow

For large sparse baskets, keep data sparse through pandas sparse extension arrays:

```python
te = TransactionEncoder()
csr = te.fit_transform(transactions, sparse=True)
df_sparse = pd.DataFrame.sparse.from_spmatrix(csr, columns=te.columns_)

itemsets = fpgrowth(df_sparse, min_support=0.01, use_colnames=True)
```

Notes:

- Do not pass the raw CSR matrix directly to `fpgrowth`/`apriori`/`fpmax`/`hmine`; wrap it as a pandas DataFrame.
- String column labels are safest for sparse DataFrames.
- Sparse storage helps input memory, but frequent itemset output can still grow combinatorially.

## 7. Threshold tuning and empty-result recovery

When itemsets are empty:

1. Check single-item supports:
   ```python
   single_support = df.astype(float).mean(axis=0).sort_values(ascending=False)
   print(single_support.head(20))
   ```
2. Set `min_support` no higher than the largest expected singleton or pair support.
3. Temporarily use `max_len=1` or `max_len=2` to separate singleton support problems from combination explosion.
4. Confirm the DataFrame is not all false/zero and that rows represent transactions rather than items.
5. If the data is nullable, use `fpgrowth(..., null_values=True)` or `fpmax(..., null_values=True)`.

When rules are empty:

1. Confirm the itemset table is not empty and includes itemsets of length at least 2.
2. Lower `min_threshold`, or threshold on `support` first.
3. Use a complete itemset table from `apriori`, `fpgrowth`, or `hmine`; avoid `fpmax` for ordinary rule metrics.
4. Inspect the maximum metric value before choosing a threshold:
   ```python
   rules = association_rules(itemsets, num_itemsets=len(df), metric="confidence", min_threshold=0.0)
   print(rules[["support", "confidence", "lift"]].describe())
   ```

## 8. Maximal itemsets plus rules

`fpmax` is useful when the required output is a compact set of maximal frequent itemsets. It intentionally omits non-maximal subsets. For association rules:

- Prefer re-mining with `fpgrowth`/`apriori`/`hmine` to get complete subset supports.
- If only combined support is needed and missing metrics are acceptable, use:
  ```python
  rules = association_rules(fpmax_itemsets, num_itemsets=len(df), support_only=True)
  ```
  Non-support metric columns will be `NaN`.

## 9. Smoke-test the installed package

Run the bundled deterministic smoke script:

```bash
python scripts/frequent_patterns_smoke.py --algorithm all
```

Expected behavior: it prints the encoded one-hot shape, itemset tables for `apriori`, `fpgrowth`, `fpmax`, and `hmine`, and association-rule tables. `fpmax` uses support-only rules because maximal itemsets are not a complete itemset lattice.
