---
name: visualization-and-results
description: "Handle CellTypist AnnotationResult exports, AnnData insertion,
  UMAP plots, and dotplots safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Visualization and Results

Use this sub-skill after a CellTypist annotation already produced an `AnnotationResult` and the user needs summaries, exported tables, AnnData metadata, UMAP figures, or prediction-vs-reference dotplots.

## Route Here When

- The user asks what is inside `predictions.predicted_labels`, `predictions.decision_matrix`, `predictions.probability_matrix`, or `predictions.adata`.
- The task is to export CSV or Excel tables with `AnnotationResult.to_table()`.
- The task is to insert labels, confidence scores, decision scores, or probabilities into AnnData with `AnnotationResult.to_adata()`.
- The task is to create CellTypist UMAP plots with `AnnotationResult.to_plots()` or compare predictions against manual labels/clusters with `celltypist.dotplot()`.
- The task is to debug missing `majority_voting`, missing `conf_score`, dotplot reference mismatches, output folder errors, or slow UMAP computation.

## Route Elsewhere

- Generate the `AnnotationResult` with `celltypist.annotate()` in [annotation-workflows](../annotation-workflows/SKILL.md).
- Download, inspect, subset, convert, or extract markers from models in [model-management](../model-management/SKILL.md).
- Interpret training artifacts or custom model outputs in [training-and-custom-models](../training-and-custom-models/SKILL.md).

## Working Pattern

1. Inspect the result shape first: `predictions`, `predictions.predicted_labels.head()`, and `predictions.summary_frequency(by="predicted_labels")`.
2. Choose the output form: `to_table()` for files, `to_adata()` for downstream Scanpy workflows, `to_plots()` for quick UMAP files, or `celltypist.dotplot()` for comparing predictions to manual labels/clusters.
3. Decide whether the workflow uses raw labels (`predicted_labels`) or majority-voted labels (`majority_voting`); do not request majority-voting confidence or dotplots unless that column exists.
4. Validate exported artifacts with [scripts/result_shape_check.py](scripts/result_shape_check.py) before plotting or handing files downstream.
5. Use [references/troubleshooting.md](references/troubleshooting.md) when an output folder, majority-voting column, reference labels, order lists, or UMAP step fails.

## References

- [Result objects and exports](references/result-objects.md): `AnnotationResult` attributes, `summary_frequency()`, `to_table()`, and `to_adata()`.
- [Plotting and dotplots](references/plotting-and-dotplot.md): `to_plots()` UMAP behavior, `celltypist.dotplot()` semantics, order/filter behavior, and interpretation.
- [Troubleshooting](references/troubleshooting.md): focused fixes for output folders, majority voting, UMAP compute, dotplot label mismatches, and shape validation.
