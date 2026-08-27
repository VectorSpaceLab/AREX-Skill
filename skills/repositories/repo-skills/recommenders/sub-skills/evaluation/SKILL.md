---
name: evaluation
description: "Compute and troubleshoot Microsoft Recommenders offline metrics
  for rating prediction, top-k ranking, diversity, novelty, serendipity, and
  optional Spark evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Evaluation

Use this sub-skill when a user has true interactions and model predictions and needs Recommenders metrics, metric selection guidance, dataframe column checks, or ranking/top-k troubleshooting.

## Backend truth for this skill

- Verified in the base CPU scope: Python evaluation module import and metric signatures for rating, ranking, diversity, novelty, serendipity, and top-k helpers.
- Optional and not verified in this CPU scope: Spark evaluation classes. They require `[spark]`, Java/JDK, and a working Spark session.
- Synthetic or docs-only checks cannot prove Spark metrics; keep Spark runtime evidence separate.

## Start here

- For metric signatures and required columns, read [api-reference.md](references/api-reference.md).
- For rating, ranking, diversity, novelty, and Spark metric recipes, read [workflows.md](references/workflows.md).
- For common metric errors and fixes, read [troubleshooting.md](references/troubleshooting.md).
- To run a tiny no-network metric smoke check, execute:

```bash
python sub-skills/evaluation/scripts/metrics_tiny_smoke.py
```

Run the command from the generated skill root, or adapt the script path to the installed skill location.

## Route elsewhere

- Loading, splitting, validating, and filtering interaction data belongs in [data-preparation](../data-preparation/SKILL.md).
- Fitting models and generating predictions or recommendations belongs in [modeling](../modeling/SKILL.md).
- Benchmark loops, hyperparameter sweeps, and cloud logging belong in [operations-and-tuning](../operations-and-tuning/SKILL.md).

## Working rules

1. Decide whether the task is rating prediction, top-k ranking, classification, or beyond-accuracy evaluation.
2. Ensure true and predicted dataframes share compatible `userID` and `itemID` dtypes before calling metrics.
3. For rating metrics, predictions should align with true pairs and include `prediction`.
4. For ranking metrics, predictions should represent candidate item scores per user; remove seen training items upstream when evaluating recommendation quality.
5. Keep `k`, `threshold`, `relevancy_method`, `score_type`, and custom column names explicit in reports.
6. Use Spark metrics only when the user is already in a verified Spark environment.
