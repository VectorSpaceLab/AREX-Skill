---
name: feature-workflows
description: "Use mlxtend feature selection, feature extraction, preprocessing,
  and transaction encoding workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Feature workflows

Use this sub-skill when the task is to prepare model inputs with mlxtend feature selectors, extraction transformers, transaction one-hot encoders, or preprocessing helpers.

## Start here

- Use [references/api-reference.md](references/api-reference.md) for verified signatures, attributes, and parameter constraints.
- Use [references/workflows.md](references/workflows.md) for selector, extraction, preprocessing, and transaction encoding recipes.
- Use [references/data-formats.md](references/data-formats.md) for accepted ndarray/DataFrame/list-of-lists schemas and metric/one-hot output shapes.
- Use [references/troubleshooting.md](references/troubleshooting.md) before changing code when selectors, scorers, column names, sparse data, or transaction encodings fail.
- Run [scripts/feature_workflows_smoke.py](scripts/feature_workflows_smoke.py) for a deterministic CPU smoke check of the installed APIs.

## Owned APIs

- Feature selection: `SequentialFeatureSelector`, `ExhaustiveFeatureSelector`, `ColumnSelector`.
- Feature extraction: `PrincipalComponentAnalysis`, `LinearDiscriminantAnalysis`, `RBFKernelPCA`.
- Preprocessing: `TransactionEncoder`, `DenseTransformer`, `MeanCenterer`, `CopyTransformer`, `one_hot`, `minmax_scaling`, `standardize`, `shuffle_arrays_unison`.

## Boundaries

- After `TransactionEncoder` produces one-hot transaction data, route itemset mining and association rules to [../frequent-patterns/SKILL.md](../frequent-patterns/SKILL.md).
- Route estimator/ensemble construction details to [../estimators-and-ensembles/SKILL.md](../estimators-and-ensembles/SKILL.md); this sub-skill only shows how estimators are passed into selectors.
- Route plotting of SFS/EFS metric dictionaries, PCA graphics, and other visualization tasks to [../plotting-and-utilities/SKILL.md](../plotting-and-utilities/SKILL.md).

## Operating rules

1. Treat selectors as sklearn-style transformers: fit on `X, y`, inspect selected-feature attributes, then call `transform` or `fit_transform` to reduce `X`.
2. Prefer pandas `DataFrame` inputs when feature names, string `fixed_features`, or string `feature_groups` matter; use ndarray integer indices otherwise.
3. Keep `feature_groups` exhaustive and non-overlapping. If `fixed_features` intersects a group, include all members of that group in `fixed_features`.
4. Use `ExhaustiveFeatureSelector` only for small feature/group counts; it evaluates all combinations between `min_features` and `max_features`.
5. Keep sparse data sparse until an API requires dense arrays; use `DenseTransformer` deliberately because densification can multiply memory use.
6. Keep transaction data as `list[list[item]]` until `TransactionEncoder`; preserve `encoder.columns_` when building pandas one-hot DataFrames.

## Safe smoke

From this sub-skill directory or any environment with mlxtend installed:

```bash
python scripts/feature_workflows_smoke.py --task all
```

The smoke script uses tiny in-memory sklearn/numpy/pandas examples, writes no files, does not download data, and does not depend on a source checkout.
