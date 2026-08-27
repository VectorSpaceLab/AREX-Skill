---
name: data-pipelines
description: "Prepare GluonTS datasets from pandas, list, JSON Lines, and
  optional Arrow inputs; split entries into train/test windows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# GluonTS data-pipelines sub-skill

Use this sub-skill when a task needs GluonTS `Dataset` objects, `DataEntry` validation, or train/test windows before modeling, transformation, or evaluation.

## Route by task

- **Pandas or in-memory tables:** read [references/data-formats.md](references/data-formats.md#pandasdataset) and [references/workflows.md](references/workflows.md#pandasdataset-recipes).
- **Long dataframes with item/static/dynamic columns:** read [references/data-formats.md](references/data-formats.md#long-dataframes) and [references/workflows.md](references/workflows.md#long-dataframe-recipe).
- **List, JSON Lines, gzipped JSON Lines, or optional Arrow/Parquet files:** read [references/data-formats.md](references/data-formats.md#listdataset-and-filedataset) and [references/workflows.md](references/workflows.md#file-backed-datasets).
- **Train/test slicing or rolling evaluation windows:** read [references/workflows.md](references/workflows.md#splitting-datasets) and use `scripts/dataset_split_smoke.py` as the local sanity check.
- **Validation failures or shape/frequency errors:** read [references/troubleshooting.md](references/troubleshooting.md).

## Safe smoke check

After installing `gluonts` with its base dependencies, run:

```bash
python sub-skills/data-pipelines/scripts/dataset_split_smoke.py
```

The script creates a tiny pandas-backed dataset, splits off the trailing prediction horizon, validates generated input/label entries, and prints a concise success summary. It performs no network, plotting, downloads, training, or checkout-relative reads.

## Boundaries

This sub-skill covers dataset construction and splitting only. Use sibling sub-skills for transforms/time features, estimator or predictor training, forecast evaluation, and deployment/extension adapters. MXNet-specific workflows are legacy/optional and are not verified by this data-pipeline guidance.
