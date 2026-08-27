# API Reference: Structured Label Issues

This reference lists the stable direct cleanlab APIs owned by this sub-skill. Use the family references for workflow recipes and [`data-formats.md`](data-formats.md) for schemas.

## Token classification

Import from `cleanlab.token_classification` modules.

| Function | Signature summary | Returns | Use when |
|---|---|---|---|
| `filter.find_label_issues` | `(labels, pred_probs, *, return_indices_ranked_by="self_confidence", low_memory=False, **kwargs)` | `list[tuple[int, int]]` token coordinates sorted by issue likelihood | Estimate token-level label issues automatically. |
| `rank.get_label_quality_scores` | `(labels, pred_probs, *, tokens=None, token_score_method="self_confidence", sentence_score_method="min", sentence_score_kwargs={})` | `(sentence_scores, token_scores)` where sentence scores are `(N,)` and token scores are a list of pandas Series | Rank sentences and inspect per-token quality scores. |
| `rank.issues_from_scores` | `(sentence_scores, *, token_scores=None, threshold=0.1)` | token tuple list if `token_scores` is supplied, otherwise sentence indices | Convert scores to review candidates using a threshold. |
| `summary.display_issues` | `(issues, tokens, *, labels=None, pred_probs=None, exclude=[], class_names=None, top=20)` | `None` | Print/highlight token issues in their sentences. |
| `summary.common_label_issues` | `(issues, tokens, *, labels=None, pred_probs=None, class_names=None, top=10, exclude=[], verbose=True)` | pandas DataFrame | Summarize repeated token or given/predicted label-swap patterns. |
| `summary.filter_by_token` | `(token, issues, tokens)` | token tuple list | Focus review on one token string. |

Notes:

- Scoring methods accepted by token helpers include `"self_confidence"`, `"normalized_margin"`, and `"confidence_weighted_entropy"`.
- Sentence aggregation methods are `"min"` and `"softmin"`; `softmin` accepts `sentence_score_kwargs={"temperature": ...}`.
- `low_memory=True` in `find_label_issues` uses the batched path internally and warns that extra kwargs such as `n_jobs` are ignored.

## Object detection

Import from `cleanlab.object_detection` modules.

| Function | Signature summary | Returns | Use when |
|---|---|---|---|
| `filter.find_label_issues` | `(labels, predictions, *, return_indices_ranked_by_score=False, overlapping_label_check=True)` | Boolean mask of length `N`, or ranked image indices when requested | Estimate which images have object-detection label issues. |
| `rank.get_label_quality_scores` | `(labels, predictions, *, aggregation_weights=None, overlapping_label_check=True, verbose=True)` | `np.ndarray` shape `(N,)` image quality scores | Rank images; lower scores are more suspect. |
| `rank.issues_from_scores` | `(label_quality_scores, *, threshold=0.1)` | ranked image indices | Threshold image scores manually. |
| `rank.compute_overlooked_box_scores` | `(*, labels=None, predictions=None, alpha=None, high_probability_threshold=None, auxiliary_inputs=None)` | list of arrays, one score per predicted box | Diagnose likely missing annotations. |
| `rank.compute_badloc_box_scores` | `(*, labels=None, predictions=None, alpha=None, low_probability_threshold=None, auxiliary_inputs=None)` | list of arrays, one score per annotated box | Diagnose poorly located annotated boxes. |
| `rank.compute_swap_box_scores` | `(*, labels=None, predictions=None, alpha=None, high_probability_threshold=None, overlapping_label_check=True, auxiliary_inputs=None)` | list of arrays, one score per annotated box | Diagnose class swaps/conflicting overlapping labels. |
| `rank.pool_box_scores_per_image` | `(box_scores, *, temperature=None)` | `np.ndarray` image scores | Aggregate per-box scores into per-image scores. |
| `summary.visualize` | `(image, *, label=None, prediction=None, prediction_threshold=None, overlay=True, class_names=None, figsize=None, save_path=None, **kwargs)` | `None` | Overlay/show annotated and predicted boxes for one image. |
| `summary.object_counts_per_image` | `(labels=None, predictions=None, *, auxiliary_inputs=None)` | `(label_counts, prediction_counts)` | Find images with unusually many/few boxes. |
| `summary.bounding_box_size_distribution` | `(labels=None, predictions=None, *, auxiliary_inputs=None, class_names=None, sort=False)` | `(annotated_sizes, predicted_sizes)` dicts | Inspect box-area anomalies by class. |
| `summary.class_label_distribution` | `(labels=None, predictions=None, *, auxiliary_inputs=None, class_names=None)` | `(annotated_freq, predicted_freq)` dicts | Compare class frequencies. |
| `summary.get_sorted_bbox_count_idxs` | `(labels, predictions)` | sorted `(index, count)` lists | Review box-count extremes. |
| `summary.plot_class_size_distributions` | `(labels, predictions, class_names=None, class_to_show=10, **kwargs)` | `None` | Plot annotated/predicted box-size histograms. |
| `summary.plot_class_distribution` | `(labels, predictions, class_names=None, **kwargs)` | `None` | Plot annotated/predicted class distributions. |
| `summary.calculate_per_class_metrics` | `(labels, predictions, num_procs=1, class_names=None)` | per-class precision/recall/F1 dictionary | Interpret detector performance by class. |
| `summary.get_average_per_class_confusion_matrix` | `(labels, predictions, num_procs=1, class_names=None)` | per-class TP/FP/FN dictionary | Support deeper object-detection review. |

Notes:

- `aggregation_weights` may tune the overall image score across issue subtypes: `"overlooked"`, `"swap"`, and `"badloc"`. Weights must be nonnegative and sum to 1.
- `overlapping_label_check=True` penalizes near-duplicate annotated boxes with different classes. Disable only if such overlaps are expected and not label problems.
- The main issue APIs return image-level issues. Use per-box subtype score helpers plus `visualize` to inspect specific boxes.

## Semantic segmentation

Import from `cleanlab.segmentation` modules.

| Function | Signature summary | Returns | Use when |
|---|---|---|---|
| `filter.find_label_issues` | `(labels, pred_probs, *, batch_size=None, n_jobs=None, verbose=True, **kwargs)` with `downsample` kwarg | Boolean mask shape `(N,H,W)` | Estimate pixel-level label issues. |
| `rank.get_label_quality_scores` | `(labels, pred_probs, *, method="softmin", batch_size=None, n_jobs=None, verbose=True, **kwargs)` | `(image_scores, pixel_scores)` | Rank images and inspect per-pixel quality scores. |
| `rank.issues_from_scores` | `(image_scores, pixel_scores=None, threshold=0.1)` | pixel mask if `pixel_scores` is supplied, otherwise ranked image indices | Threshold scores manually. |
| `summary.display_issues` | `(issues, *, labels=None, pred_probs=None, class_names=None, exclude=None, top=None, **kwargs)` | `None` | Display issue masks, optionally alongside label/prediction masks. |
| `summary.common_label_issues` | `(issues, labels, pred_probs, *, class_names=None, exclude=None, top=None, verbose=True)` | pandas DataFrame | Summarize given/predicted class swaps across pixels. |
| `summary.filter_by_class` | `(class_index, issues, labels, pred_probs)` | Boolean mask shape `(N,H,W)` | Focus on issues involving one class. |

Notes:

- `method="softmin"` is the default scoring method and returns image/pixel scores without calling the full issue finder.
- `method="num_pixel_issues"` calls `find_label_issues`; its `downsample`, `batch_size`, and `n_jobs` knobs control runtime/memory.
- `downsample` must divide both image height and width.

## Source-script inventory note

No source notebook or native pytest file is bundled directly. The tutorial notebooks rely on external downloads and interactive visuals, and the native tests include pytest scaffolding/random generators. The bundled smoke script uses tiny deterministic fixtures distilled from those public examples/tests instead.
