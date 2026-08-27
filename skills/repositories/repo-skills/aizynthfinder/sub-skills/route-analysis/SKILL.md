---
name: route-analysis
description: "Inspect AiZynthFinder output files, route collections, reaction
  trees, route scores, clustering, images, and downstream summaries without
  rerunning a search."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Route Analysis

Use this sub-skill when the task is to read, summarize, score, render, compare, cluster, or troubleshoot existing AiZynthFinder route-analysis outputs.

## Use This For

- Loading `output.json.gz`, HDF5 table outputs, line-oriented checkpoint files, or `trees.json` route dumps.
- Explaining output columns such as `target`, `top_score`, `is_solved`, `number_of_routes`, `top_scores`, `stock_info`, and `trees`.
- Inspecting `ReactionTree`, `RouteCollection`, `TreeAnalysis`, and built-in scorer behavior for existing routes.
- Rendering route images from serialized reaction trees and diagnosing image/PIL/schema failures.
- Running safe local summaries with `scripts/summarize_aizynth_output.py`.
- Explaining clustering, route distance matrices, combined reaction trees, Pareto fronts, and rescoring caveats.

## Route Elsewhere

- Run new searches, resume searches, or interpret search checkpoint generation: use `planning-workflows`.
- Build or repair configs, stocks, model paths, policy/filter settings, or data files: use `configuration-and-data`.
- Implement custom scorers, custom route-distance backends, or extension classes: use `extension-and-development`.
- If malformed output appears caused by interrupted CLI execution or bad input/config, start here for file triage, then route to `planning-workflows` or `configuration-and-data` once the cause is clear.

## Quick Workflow

1. Identify the output type: pandas table (`.json`, `.json.gz`, `.hdf`, `.h5`, `.hdf5`), checkpoint line JSON, or standalone tree JSON.
2. For table outputs, load with pandas using table orientation for JSON and key `table` for HDF5; inspect expected columns before accessing `trees`.
3. For route rendering, convert each tree dictionary with `ReactionTree.from_dict(tree_dict)`, then use `to_image()`, `to_json()`, or `to_dict()`.
4. For scoring and collection-level work, build or receive `RouteCollection` objects from `ReactionTree` instances and apply `compute_scores()`, `rescore()`, `distance_matrix()`, or `cluster()` only when dependencies and valid tree schemas are present.
5. For a safe first pass over an output file, run the bundled summarizer:

```bash
python scripts/summarize_aizynth_output.py output.json.gz
```

Add `--write-tree-summary trees-summary.json` only when the user explicitly asks to write tree summaries.

## References

- Output formats, pandas loading recipes, columns, checkpoint semantics, and tree structures: `references/output-formats.md`.
- Verified route-analysis APIs and lifecycle patterns: `references/api-reference.md`.
- Built-in scorer names, rescoring, distance matrices, and clustering caveats: `references/scoring-and-clustering.md`.
- Failures for parsing, missing optional dependencies, rendering, tree schemas, and partial outputs: `references/troubleshooting.md`.
