---
name: data-preparation
description: "Prepare, validate, split, and transform interaction datasets for
  Microsoft Recommenders workflows, including pandas, sparse, LibFFM, and
  optional Spark paths."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data Preparation

Use this sub-skill when a user needs to load recommendation datasets, validate interaction columns, choose a train/test splitter, create negative samples, convert dataframe formats, or prepare sparse matrices before modeling or evaluation.

## Backend truth for this skill

- Verified in the base CPU scope: pandas/numpy dataframe utilities, Python splitters, sparse `AffinityMatrix`, LibFFM conversion signatures, and MovieLens helper import/signature checks.
- Optional and not verified in this CPU scope: PySpark splitters and Spark dataframe loaders. They require the `[spark]` extra plus a working Java/Spark/PySpark runtime.
- Dataset download helpers may use network access. For no-network tasks, prefer user-provided small fixtures or bundled validation scripts.

## Start here

- For validated API signatures and defaults, read [api-reference.md](references/api-reference.md).
- For end-to-end data preparation recipes, read [workflows.md](references/workflows.md).
- For column contracts and dataframe/sparse/LibFFM layouts, read [data-formats.md](references/data-formats.md).
- For common failures, read [troubleshooting.md](references/troubleshooting.md).
- To check whether a small interactions CSV is ready for common Recommenders workflows, run:

```bash
python sub-skills/data-preparation/scripts/validate_interactions.py --input interactions.csv --require-rating --require-timestamp
```

Run the command from the generated skill root, or adapt the script path to the installed skill location.

## Route elsewhere

- Choosing or fitting algorithms belongs in [modeling](../modeling/SKILL.md).
- Computing RMSE, MAP, nDCG, diversity, novelty, or serendipity belongs in [evaluation](../evaluation/SKILL.md).
- Hyperparameter sweeps, benchmark loops, Databricks, AzureML, AKS, and environment diagnostics belong in [operations-and-tuning](../operations-and-tuning/SKILL.md).

## Working rules

1. Normalize the user's dataframe contract before choosing a splitter. Default columns are `userID`, `itemID`, `rating`, `timestamp`, and `prediction`.
2. For implicit-feedback workflows, make the positive event column explicit. Use `rating` or a custom label consistently; do not mix `feedback`, `label`, and `rating` without a mapping.
3. Use random splits for quick smoke tests, chronological splits when timestamps encode order, and stratified splits when each user or item needs representation in train/test.
4. Check minimum interactions before stratifying. A user or item with too few rows can make a split impossible or misleading.
5. Treat Spark loaders/splitters as optional. Do not claim Spark validation unless PySpark and Java are actually available.
6. Do not instruct future agents to open original notebooks or tests; the recipes and helper here are the self-contained replacements.
