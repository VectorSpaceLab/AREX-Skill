# Datalab issue types

## How to read Datalab results

- `get_issue_summary()` is the dataset-level view.
- `get_issues()` is the per-example view.
- Lower quality scores always mean more severe issues.
- Scores are comparable across examples for the same issue type, but **not** across different issue types.
- For dataset-level checks such as non-IID, class imbalance, underperforming groups, and spurious correlations, look at the summary or `info` first.

## Base selection rules

- `issue_types=None` runs the task default list.
- `issue_types={}` runs nothing.
- `features` and `knn_graph` can be reused across issue types; when both are provided, `knn_graph` wins.
- `data_valuation` is supported, but request it explicitly when you want it.

## Built-in Datalab issue types

| Issue type | Tasks | Main inputs | Best readout | Notes |
| --- | --- | --- | --- | --- |
| `label` | classification, regression, multilabel | Classification: `pred_probs` or `features`; regression: 1D predictions or `features`; multilabel: `pred_probs` | `get_issues("label")`, `get_issue_summary("label")` | Flags likely mislabeled examples. `get_issues()` adds `given_label` and `predicted_label`. |
| `outlier` | classification, regression, multilabel | `features`, `knn_graph`; classification can also use `pred_probs` | both | Flags atypical or low-confidence examples. Lower scores mean more unusual examples. |
| `near_duplicate` | classification, regression, multilabel | `features` or `knn_graph` | both | Returns `near_duplicate_sets` and `distance_to_nearest_neighbor`. Exact duplicates score `0`. |
| `non_iid` | classification, regression, multilabel | `features` or `knn_graph`; classification can also use `pred_probs` | summary first | Dataset-level IID diagnostic. Per-example scores are secondary hints. Lower summary scores mean stronger evidence of non-IID structure. |
| `class_imbalance` | classification only | labels only | summary first | Dataset-level class-frequency check. Use `get_issue_summary("class_imbalance")` to inspect the overall imbalance score. |
| `underperforming_group` | classification only | `pred_probs` plus `features`, `knn_graph`, or `cluster_ids` | summary first | Dataset-level slice check. You can pass `cluster_ids` to skip clustering. |
| `data_valuation` | classification, regression | `features` or `knn_graph` plus labels | both | KNN-Shapley style valuation. Lower scores mean the example contributes less. Request it explicitly. The multilabel registry entry exists, but current list-of-lists label handling can be fragile, so verify before relying on it. |
| `null` | classification, regression, multilabel | `features` | both | Finds rows with null values. Full-null rows are particularly important; reports also call out partial null rows. |

## Image issue types

These are only available when `image_key` is set on a Hugging Face `datasets.Dataset`.

| Image issue type | What it means | How to request it |
| --- | --- | --- |
| `dark` | Too dark overall. | `issue_types={"image_issue_types": {"dark": {}}}` |
| `light` | Too bright overall. | `issue_types={"image_issue_types": {"light": {}}}` |
| `low_information` | Low visual information / content. | `issue_types={"image_issue_types": {"low_information": {}}}` |
| `odd_aspect_ratio` | Strange image shape. | `issue_types={"image_issue_types": {"odd_aspect_ratio": {}}}` |
| `odd_size` | Unusual image size. | `issue_types={"image_issue_types": {"odd_size": {}}}` |
| `grayscale` | Grayscale when color is expected. | `issue_types={"image_issue_types": {"grayscale": {}}}` |
| `blurry` | Blurry or unfocused image. | `issue_types={"image_issue_types": {"blurry": {}}}` |

Notes:
- The nested `image_issue_types` dict is the clean way to request only a subset of image checks.
- If `image_key` is set and `issue_types` is omitted, Datalab includes the default image checks too.
- Image issue rows appear in `issue_summary` just like other Datalab issues.

## Spurious correlations

`spurious_correlations` is an image-only analysis that compares image-property scores against labels.

- Request it with `issue_types={"spurious_correlations": {}}` or `issue_types={"spurious_correlations": {"threshold": 0.2}}`.
- It only works after image-property scores have already been computed.
- It lives in `lab.get_info("spurious_correlations")`, not in `lab.issue_summary`.
- The default threshold is `0.3`; lower scores indicate stronger correlation.

## Interpretation reminders

- `report()` may show both the dataset-level summary and the top per-example rows.
- For label, outlier, near-duplicate, and null checks, per-example rows are the primary outputs.
- For non-IID, class imbalance, underperforming groups, and spurious correlations, the summary or info dict is usually the first thing to inspect.
