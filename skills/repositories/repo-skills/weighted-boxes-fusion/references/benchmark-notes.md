# Benchmark notes

## Read this when

Use this page only when a user explicitly asks about reproducing the benchmark families described by Weighted-Boxes-Fusion. The benchmark material is useful context for method selection, but it is not part of the default smoke path.

## Benchmark families

| Benchmark family | What it demonstrates | Extra dependencies | External data | Runtime status in this skill |
| --- | --- | --- | --- | --- |
| Open Images Dataset (OID) | Compares NMS, Soft-NMS, NMW, and WBF for a five-model object-detection ensemble. | `pandas`, `map_boxes`, and the base package dependencies. | OID prediction CSVs and labels from an external release artifact. | Reference-only; not bundled as a runnable helper because it is data-heavy and benchmark-scale. |
| COCO validation | Applies WBF-style ensembling to COCO detector predictions and evaluates with COCO metrics. | `pandas`, `pycocotools`, and the base package dependencies. | COCO annotations plus prediction files. | Reference-only; not bundled as a runnable helper because it requires COCO data and optional evaluation tooling. |
| Feedback Prize / NLP spans | Uses 1D WBF to combine token-span predictions for an NLP competition. | `pandas` and base package dependencies. | Model prediction CSVs and validation labels. | Concepts are distilled into the 1D sub-skill; full benchmark execution remains optional and external-data-bound. |

## What to carry into normal package use

- OID and COCO show why WBF is a good default when multiple detectors predict overlapping boxes and you want fused coordinates instead of pure suppression.
- The NLP benchmark shows how token spans can be normalized into 1D intervals, fused with `weighted_boxes_fusion_1d`, then mapped back to inclusive token strings.
- The benchmark scripts are dataset-scale workflows. For package integration, start with the bundled smoke helpers and a small validation sample instead of downloading full benchmark inputs.

## Reproduction constraints

If a user explicitly wants benchmark reproduction, make a separate, task-specific plan that includes:

1. the chosen benchmark family;
2. the exact external data files and permissions required;
3. optional dependencies such as `pycocotools` or `map_boxes` when needed;
4. an expected runtime and storage budget;
5. a clean output directory outside the generated skill tree.

Do not treat benchmark reproduction as proof that a normal 2D, 1D, or 3D fusion task needs those optional dependencies.
