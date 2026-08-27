---
name: outlier
description: "Route cleanlab outlier and OOD scoring from features or pred_probs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Outlier

Use this sub-skill for direct `cleanlab.outlier.OutOfDistribution` workflows.

## Route here when
- You have numeric feature embeddings and want KNN-based outlier scores.
- You have classifier `pred_probs` and want uncertainty-based outlier scores.
- You need to rank the most atypical points from a score vector.

## Route elsewhere
- Broader dataset audits, `lab.find_issues(...)`, or `get_issues("outlier")` in a mixed audit -> [`../datalab/SKILL.md`](../datalab/SKILL.md).
- Standard noisy-label or dataset-health workflows -> [`../classification/SKILL.md`](../classification/SKILL.md).
- Multiannotator workflows -> [`../multiannotator/SKILL.md`](../multiannotator/SKILL.md).
- Multi-label/regression or structured-output label issues -> [`../tabular-label-issues/SKILL.md`](../tabular-label-issues/SKILL.md) or [`../structured-label-issues/SKILL.md`](../structured-label-issues/SKILL.md).

## Core contract
- Constructor: `OutOfDistribution(params: Optional[dict] = None) -> None`
- Public methods: `fit`, `score`, `fit_score`
- Lower scores mean more atypical examples.
- Rank worst scores with `cleanlab.rank.find_top_issues`.

## Cross-links
- Datalab uses the same outlier ideas when you want a broader audit.
- `cleanlab.rank.find_top_issues` is the shared ranking helper used by classification workflows too.

## Read/run next
- Read [API reference](references/api-reference.md) when you need constructor, method, parameter, and return-shape details.
- Read [Workflows](references/workflows.md) when choosing feature-based versus `pred_probs`-based scoring or using Datalab as a wrapper.
- Read [Troubleshooting](references/troubleshooting.md) when shape, label, metric, fitting, or interpretation errors arise.
- Run [Smoke helper](scripts/smoke_outlier.py) to verify tiny feature-based and `pred_probs`-based outlier cases.
