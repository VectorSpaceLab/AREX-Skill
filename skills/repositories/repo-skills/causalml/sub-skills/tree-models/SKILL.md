---
name: tree-models
description: "Tree-based causal and uplift model workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# tree-models

Use this sub-skill for causal trees, uplift trees, tree ensembles, tree plots, and tree persistence.

## Route here when the request is about
- `CausalTreeRegressor` or `CausalRandomForestRegressor`
- `UpliftTreeClassifier` or `UpliftRandomForestClassifier`
- tree visualization or tree-string rendering
- `save` / `load` for tree models
- compiled-extension or tree-import failures

## Open the matching reference
- [Causal trees](references/causal-trees.md)
- [Uplift trees](references/uplift-trees.md)
- [Troubleshooting](references/troubleshooting.md)

## Guardrails
- `CausalRandomForestRegressor` has no `fit_predict`; use `fit(...)` and then `predict(...)`.
- `UpliftTreeClassifier` uses `fill(...)` and `prune(...)` for validation-set updates.
- `uplift_tree_string(...)` prints the ASCII tree, and `uplift_tree_plot(...)` returns a graph object.
- Keep class-specific persistence, visualization, and failure-handling details in the bundled references.
