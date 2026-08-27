---
name: feature-inspection-and-selection
description: "Inspect Featuretools installation and primitive catalogs,
  recommend primitives, and prune feature matrices."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Feature Inspection And Selection

Use this sub-skill when the task is about understanding what Featuretools is installed, which primitives are available, which primitives are recommended, or which generated columns should be removed from a feature matrix.

## Route Here For

- Printing package and environment information with `show_info`.
- Listing or summarizing primitive catalogs.
- Recommending primitives for a single-table entityset.
- Removing low-information, highly null, single-value, or highly correlated columns.
- Cleaning a feature matrix after DFS or before model training.

## Start With These References

- `../../references/api-reference.md`: the discovery and selection signatures.
- `references/workflows.md`: when to inspect first and when to prune.
- `references/troubleshooting.md`: threshold, missing-column, and recommendation-limit recovery notes.
- `scripts/selection_smoke.py`: a tiny self-check for catalog discovery and matrix pruning.

## Boundaries

- Stay inside package info, primitive discovery, primitive recommendation, and matrix pruning.
- Route raw EntitySet setup to `../entitysets-and-data/`.
- Route DFS, feature-matrix creation, and encoding to `../deep-feature-synthesis/`.
- Route custom primitive authoring, feature descriptions, graphs, and persistence to `../primitives-and-feature-definitions/`.

## Minimal Workflow

1. Start with `show_info` or `list_primitives` when the user asks what is installed.
2. Use `summarize_primitives` when a compact primitive table would be easier to read than the raw list.
3. Use `get_recommended_primitives` only on a single-table entityset.
4. Prune the matrix with the selection helper that matches the failure mode: null-heavy, low-information, single-value, or highly correlated.

## Common Decision Points

- Keep the single-table requirement in mind for `get_recommended_primitives`.
- Use `features=None` when you only need a pruned matrix; pass the feature list when you need the definitions aligned with the matrix.
- Use `features_to_check` and `features_to_keep` only when you need a more targeted correlated-feature pass.
- Treat `replace_inf_values` as a cleanup helper for matrices that contain infinities before model training.

## Quality Bar

Future agents should be able to explain what is installed, discover useful primitives, and prune a noisy feature matrix without reopening the original repository.
