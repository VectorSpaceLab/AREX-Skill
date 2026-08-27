---
name: search
description: "Routes Once-for-All accuracy-predictor, FLOPs/latency-table, and
  evolutionary architecture-search workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Search

Use this sub-skill when the user wants to search for a good OFA subnet using the tutorial-style accuracy predictor, latency or FLOPs tables, or evolutionary search loop.

## Triggers

Choose this route for requests like:

- "search for the best subnet"
- "run the OFA architecture search"
- "use the accuracy predictor"
- "build a FLOPs tradeoff curve"
- "use the latency table"
- "adapt the notebook search workflow"

## Included workflows

- Loading the search helpers from `ofa.tutorial`.
- Running a small offline search smoke with a dummy efficiency predictor.
- Running predictor-driven search with FLOPs or latency constraints.
- Interpreting the best-info tuple returned by `EvolutionFinder`.
- Reading the notebook-derived search flow for the published tutorial.

## Excluded workflows

- Model loading and ImageNet evaluation. Route that to `sub-skills/inference/`.
- Distributed training. It is intentionally out of scope for this generated skill.

## Read next

- `references/api-reference.md` for constructors and return-value contracts.
- `references/workflows.md` for the published search flow and the bundled offline smoke.
- `references/troubleshooting.md` for download, dependency, and constraint issues.

## Bundled helper

- `scripts/tiny_search.py` — offline smoke for `AccuracyPredictor` plus the evolutionary loop.

## Typical flow

1. Decide whether the user needs a smoke, a FLOPs search, or a latency-constrained search.
2. Load the accuracy predictor and the selected efficiency predictor.
3. Run the bundled smoke script for a quick offline verification, or use the workflow reference for the real notebook-style search.
4. Inspect the returned best sample, efficiency value, and predicted accuracy.

## Practical notes

- `AccuracyPredictor(pretrained=False)` is enough for a smoke check.
- Real FLOPs or latency search may need optional downloads or a cached lookup table.
- The `best_info` tuple from `EvolutionFinder` contains the predicted accuracy, the sample dict, and the efficiency value.
