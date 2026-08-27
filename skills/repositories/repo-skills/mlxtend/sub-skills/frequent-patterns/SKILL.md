---
name: frequent-patterns
description: "Mine frequent itemsets and association rules from transaction data
  with mlxtend frequent_patterns."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Frequent Patterns

Use this sub-skill when the task involves market-basket or transaction mining with `mlxtend.frequent_patterns`: frequent itemsets, maximal itemsets, association rules, support/confidence/lift-style metrics, null-aware FP mining, sparse one-hot data, or threshold diagnosis.

## Route first

- Start with [references/data-formats.md](references/data-formats.md) when the input is raw transactions, one-hot pandas data, sparse data, nullable data, or previously mined itemsets/rules.
- Use [references/api-reference.md](references/api-reference.md) for verified function signatures, return columns, algorithm differences, and metric names.
- Use [references/workflows.md](references/workflows.md) for transaction-to-rules recipes, algorithm selection, rule filtering, null handling, and support/threshold tuning.
- Use [references/troubleshooting.md](references/troubleshooting.md) for invalid inputs, missing columns, empty results, metric errors, nullable/sparse warnings, and memory growth.
- Run [scripts/frequent_patterns_smoke.py](scripts/frequent_patterns_smoke.py) to verify that the installed package can encode transactions, mine itemsets, and generate rules on a tiny deterministic dataset.

## Boundaries

- Prefer `TransactionEncoder` only as the upstream route from list-of-lists transactions into a one-hot pandas DataFrame. For broader preprocessing and transformer behavior, route to [../feature-workflows/SKILL.md](../feature-workflows/SKILL.md).
- Do not handle plotting or visualization here. Route rule plots, heatmaps, and Matplotlib utilities to [../plotting-and-utilities/SKILL.md](../plotting-and-utilities/SKILL.md).
- Keep downstream mining code package-based; the runtime workflow must use only installed package APIs and bundled skill files.

## Fast decision map

| Goal | Primary API | Notes |
|---|---|---|
| All frequent itemsets, classic candidate search | `apriori` | Supports `low_memory` and `n_jobs`; no nullable-NaN mode. |
| All frequent itemsets, usually faster on sparse/large baskets | `fpgrowth` | FP-tree based; supports `null_values=True`. |
| Only maximal frequent itemsets | `fpmax` | Compact output; not a full subset lattice for normal rule metrics. |
| All frequent itemsets via H-Mine | `hmine` | Alternative frequent-itemset miner; no nullable-NaN mode. |
| Rules from complete frequent itemsets | `association_rules` | Requires `support` and `itemsets`; use full itemset output unless `support_only=True`. |
| Raw transactions to one-hot DataFrame | `TransactionEncoder` | Create `pd.DataFrame(te.fit_transform(transactions), columns=te.columns_)`. |
