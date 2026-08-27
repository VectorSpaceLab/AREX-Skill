---
name: evaluation
description: "Score retrieved duplicate maps and plot duplicate groups in imagededup."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# evaluation

Use this sub-skill when the user already has duplicate results and wants to score them or visualize them.

## Best-fit tasks

- Evaluate a retrieved duplicate map against a symmetric ground-truth map.
- Compute MAP, NDCG, Jaccard, precision, recall, F1, and support.
- Plot one image together with its duplicates.
- Understand whether a duplicate map is valid before scoring it.

## Read this sub-skill first when the request mentions

- `evaluate`
- `plot_duplicates`
- ground truth or retrieved maps
- MAP, NDCG, Jaccard, precision, recall, F1, or support
- classification metrics or information-retrieval metrics
- duplicate visualization

## Workflow overview

1. Confirm that both maps refer to the same filenames.
2. Confirm the duplicate relationships are symmetric.
3. Choose the metric family or let `evaluate` return them all.
4. Plot only after the filename exists in the duplicate map and the duplicate list is non-empty.

## Common decisions

- Use `metric='all'` when you want every metric in one pass.
- Use `metric='classification'` when you want per-class precision/recall/F1.
- Use `metric='map'`, `metric='ndcg'`, or `metric='jaccard'` when you want one IR score.
- Use `plot_duplicates` when you want a visual sanity check for one image and its retrieved duplicates.

## Helpful facts

- `evaluate` requires matching keys across the ground-truth and retrieved maps.
- Both maps must be symmetric.
- Information-retrieval metrics treat each key as a query.
- Classification metrics collapse symmetric pairs into unique unordered pairs.
- `plot_duplicates` accepts a map with or without scores.
- `plot_duplicates` raises if the requested filename has no duplicates.

## Troubleshooting pointer

Read [`references/troubleshooting.md`](references/troubleshooting.md) for symmetry validation failures, missing-key errors, empty duplicate lists, and headless plotting tips.

## Script helper

Run [`scripts/evaluate_plot_smoke.py`](scripts/evaluate_plot_smoke.py) to exercise scoring and plotting on a synthetic symmetric map.

## When to escalate elsewhere

- If you still need encodings or duplicate search, switch to the hashing or CNN sub-skill.
- If the task is only about generating hashes or feature vectors, stay out of this sub-skill.

## Good output expectations

A good evaluation-oriented answer should usually include:

- which metric family is being used
- whether the maps are symmetric and aligned
- what the returned metric types look like
- how to interpret the plot or figure output