# Troubleshooting

Use this table when a classification workflow fails fast or produces surprising metrics.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Found duplicate task ...` | Two `Task` objects share the same `name`. | Rename one task. Task names must be unique in a `MultitaskClassifier`. |
| `Unsuccessful operation ...` | An `Operation` input name does not match a prior operation, or a module raised an error. | Make sure each input refers to `'_input_'`, a previous operation name, or a valid `(op_name, field_key)` tuple. Check that the module’s input signature matches the provided values. |
| `Label ... should be torch.Tensor` | A `DictDataset` was built with non-tensor labels. | Convert labels with `torch.as_tensor(...)` before constructing the dataset. |
| `Cannot find any dataloaders with split matching train split` | No loader uses the configured training split. | Provide at least one loader whose `dataset.split` matches `train_split`, or update the trainer config. |
| `Dataloader splits must be one of ...` | A loader uses a split name outside the trainer’s configured train/valid/test set. | Rename the split or widen the trainer split settings. |
| `Unrecognized optimizer option ...` | The optimizer string is not supported. | Use `sgd`, `adam`, or `adamax`. |
| `Unrecognized lr scheduler option ...` | The lr scheduler string is not supported. | Use `constant`, `linear`, `exponential`, or `step`. |
| `Unrecognized writer option ...` | The log writer string is not supported. | Use `json` or `tensorboard`. |
| `Unrecognized batch scheduler option ...` | The batch scheduler string is not supported. | Use `sequential` or `shuffled`. |
| `checkpoint_metric must be formatted 'task/dataset/split/metric:mode'` | The checkpoint metric string is missing a field. | Provide exactly four path parts and a `:min` or `:max` suffix. |
| `Metric must be of the form 'metric_name:mode'` | One of the additional checkpoint metrics is malformed. | Use the same `metric:mode` form for each extra checkpoint metric. |
| `The metric you provided (...) is not currently implemented.` | `metric_score()` was asked for an unsupported metric name. | Use a supported metric or add a custom scorer function. |
| `Metric roc_auc is currently only defined for binary problems.` | ROC AUC was called with more than two probability columns. | Use a binary task or choose a different metric. |
| `f1 not supported for multiclass` | The plain `f1` metric was used on multiclass labels. | Use `f1_micro` or `f1_macro`. |
| `Metric ... requires access to ...` | `golds`, `preds`, or `probs` was missing for the selected metric. | Pass the required arrays to `Scorer.score()` or `metric_score()`. |
| `S, golds, preds, and probs must have the same number of elements` | Slice metrics were asked to score misaligned arrays. | Make sure the recarray and label arrays have the same length. |
| `probs must have probabilities for at least 2 classes` | `probs_to_preds()` was called on a single-class distribution. | Provide at least two classes. |
| `Could not convert abstained vote to probability` | `preds_to_probs()` received negative labels. | Remove abstains or replace them before converting to probabilities. |

## Shape and probability reminders

- `cross_entropy_with_probs` expects logits of shape `[n_examples, num_classes]` and soft labels with the same shape.
- `metric_score(..., metric='roc_auc')` expects binary probabilities.
- `Scorer` filters abstains by default for most metrics when `abstain_label` is set.
- `coverage` intentionally measures kept predictions, so it does not use the abstain filter path.

## Abstain and filtering behavior

If you want to score while ignoring unknown gold labels or abstained predictions:

- use `Scorer(abstain_label=-1)` for the standard convention,
- or call `metric_score(..., filter_dict={"golds": [-1], "preds": [-1]})` directly.

Remember that every aligned array is filtered together, so the result remains synchronized across golds, preds, and probs.

## CPU and GPU behavior

- `MultitaskClassifier(device=-1)` keeps the model on CPU.
- A non-negative device index requests CUDA, but the model falls back to CPU if CUDA is unavailable.
- `dataparallel=True` only matters when the runtime can actually wrap modules with `DataParallel`.
- The classification workflow is CPU-valid end to end; GPU is optional.

## When checkpointing does not save what you expect

Check three things first:
1. the metric key exists in the evaluation output,
2. the checkpoint metric string matches that key’s namespace,
3. the checkpoint mode is `min` or `max` and not a typo.

If the best model file is missing, the metric name is usually the fastest place to look.