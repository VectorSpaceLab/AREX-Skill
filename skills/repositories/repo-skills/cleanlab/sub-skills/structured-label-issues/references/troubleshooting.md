# Troubleshooting Structured Label Issues

Start by checking the family-specific data format in [`data-formats.md`](data-formats.md). Then use the targeted tables below.

## Routing mistakes

| Symptom | Likely cause | Fix |
|---|---|---|
| User asks for span classification | Wrong sub-skill | Route to `experimental`; span classification is intentionally excluded here. |
| User wants one broad audit/report across a dataset | Wrong abstraction | Route to `datalab` when the goal is a broad dataset audit wrapper. |
| User has one class label per row, not tokens/boxes/pixels | Wrong task family | Route to `classification` for multiclass/binary; `tabular-label-issues` for multilabel/regression. |
| User has multiple annotators per example | Wrong task family | Route to `multiannotator`. |
| User asks for outliers/OOD rather than label issues | Wrong task family | Route to `outlier`. |

## Token classification

| Symptom | Likely cause | Fix |
|---|---|---|
| Index errors or wrong token highlighted | `tokens`, `labels`, and `pred_probs` nested lengths do not match | For every sentence `i`, verify `len(tokens[i]) == len(labels[i]) == pred_probs[i].shape[0]`. |
| Scores look swapped between classes | Class order mismatch | Ensure `pred_probs[i][:, k]`, integer label `k`, and `class_names[k]` all represent the same class. |
| `class_names` output is misleading | Names not in integer-id order | Rebuild `class_names` so position `k` names class id `k`. |
| Too many `O`/background/entity-prefix confusions | Annotation policy or IOB mapping differs from model output | Decide whether to merge/normalize labels before cleanlab, or use `exclude=[(given, predicted), ...]` only for display/summaries. |
| `low_memory=True` ignores kwargs | Expected behavior | The low-memory token path uses a batched helper and warns that extra kwargs are not used. Remove unused kwargs or run without `low_memory`. |
| Sentence is flagged but displayed token is not obvious | Sentence score is an aggregate | Use token scores from `get_label_quality_scores(..., tokens=tokens)` or `find_label_issues` token tuples to localize the token. |

Interpretation reminder: token issue tuples are `(sentence_index, token_index)`. Sentence-level scores rank review priority, not every token in the sentence.

## Object detection

| Symptom | Likely cause | Fix |
|---|---|---|
| `labels and predictions length needs to match` | Different number of images in labels and predictions | Ensure both lists have length `N` and matching image order. |
| `Labels has to be a list of dicts` | Label entries are not dictionaries | Convert each image annotation to `{"bboxes": ..., "labels": ...}`. |
| Prediction format error mentioning `[x1,y1,x2,y2,pred_prob]` | Prediction class arrays do not have 5 columns | Ensure each `predictions[i][k]` has shape `(M, 5)` with the confidence/probability in the final column. |
| Empty prediction classes fail later | Empty classes represented as `[]`/`None` inconsistently | Use `np.empty((0, 5), dtype=float)` for each class with no boxes. |
| Boxes draw in the wrong location | Coordinate convention mismatch | Use `[x1, y1, x2, y2]` in the same coordinate system as the image passed to `visualize`. |
| Negative/zero-size boxes or odd box-size summaries | `x2 < x1` or `y2 < y1`, or degenerate boxes | Validate boxes before scoring; zero-area boxes are not useful review targets. |
| Many duplicate-overlap issues | Same region annotated with multiple classes | Keep `overlapping_label_check=True` if these are annotation mistakes; set `False` only if dataset policy intentionally allows conflicting overlaps. |
| `aggregation_weights` raises | Weights are negative or do not sum to 1 | Use exactly the keys `overlooked`, `swap`, `badloc`; nonnegative values summing to 1. |
| `visualize` or plot helpers fail importing matplotlib | Optional plotting dependency/backend issue | Install matplotlib or skip visualization; in scripts set `matplotlib.use("Agg")` before importing pyplot. |
| Image is flagged but exact bad box is unclear | Main APIs are image-level | Compute `compute_overlooked_box_scores`, `compute_badloc_box_scores`, and `compute_swap_box_scores`, then visually inspect low-score boxes. |

Interpretation reminder: `find_label_issues` flags images, not individual boxes. Per-box helpers are diagnostic aids for review.

## Semantic segmentation

| Symptom | Likely cause | Fix |
|---|---|---|
| `labels must have a shape of (N, H, W)` | Labels are one-hot or include an extra channel axis | Convert one-hot `(N,K,H,W)` labels with `np.argmax(labels_one_hot, axis=1)` or squeeze invalid singleton axes. |
| `pred_probs must have a shape of (N, K, H, W)` | Probabilities are channel-last or missing class dimension | Reorder with `np.moveaxis` or regenerate as class-first probabilities. |
| `labels and pred_probs must have matching dimensions for N, H, and W` | Image count or mask size mismatch | Align image order and resize/crop masks/probabilities before cleanlab. |
| Downsample error says height/width not divisible | `downsample` does not divide both `H` and `W` | Use `downsample=1` or choose a factor dividing both dimensions. |
| Small mislabeled patch is missed | Downsampling compressed away fine detail | Reduce `downsample`; use `downsample=1` for small-patch investigations. |
| Display with `exclude` raises `Provide labels to allow class exclusion` | `exclude` needs given labels | Pass `labels=labels` whenever using `exclude`. |
| Matplotlib display fails in headless environment | Interactive backend unavailable | Set `matplotlib.use("Agg")` before importing pyplot, or skip display and inspect returned masks/DataFrames. |
| Pixel mask is dense/noisy | Threshold too high or model probabilities poorly calibrated | Prefer `find_label_issues` for estimated issues; when using `issues_from_scores`, lower `threshold` for a smaller high-confidence review set. |
| `n_jobs` multiprocessing behaves unexpectedly | Platform/import limitations | Retry with `n_jobs=1`, especially in notebooks, spawned processes, or constrained CI. |

Interpretation reminder: segmentation issue masks are per-pixel `(N,H,W)`. Image scores prioritize images for review; they do not replace pixel masks.

## Cross-family prediction quality

Cleanlab can run on in-sample predictions, but label-issue quality is best with out-of-sample predictions/probabilities. If results are implausibly clean or noisy, check whether the model probabilities came from a model trained on the same labels without cross-validation/holdout protection.

## Tiny smoke helper notes

The bundled `scripts/smoke_structured_label_issues.py` sets a non-interactive matplotlib backend when display checks are enabled. It also uses deterministic toy data; passing the smoke script does not prove a user's real dataset schema is correct.
