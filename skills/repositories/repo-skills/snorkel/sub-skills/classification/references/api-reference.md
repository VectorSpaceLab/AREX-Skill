# Classification API reference

This is a compact field guide for the operating APIs used by Snorkel classification workflows.

## Data

| API | Purpose | Key defaults / notes |
| --- | --- | --- |
| `DictDataset(name, split, X_dict, Y_dict)` | Dictionary-backed dataset for inputs and labels. | Every value in `Y_dict` must be a `torch.Tensor`. `__getitem__` returns one-example dicts. `__len__` follows the first label tensor. |
| `DictDataset.from_tensors(X_tensor, Y_tensor, split, input_data_key='input_data', task_name='task', dataset_name='SnorkelDataset')` | Convenience factory for a single-input, single-task dataset. | Use when all examples share one tensor input field. |
| `collate_dicts(batch)` | Merge one-example dict pairs into a batch. | Tensor lists are stacked or padded through the classification tensor helper. |
| `DictDataLoader(dataset, collate_fn=collate_dicts, **kwargs)` | `DataLoader` wrapper for `DictDataset`. | Pass any standard `DataLoader` kwargs such as `batch_size` and `shuffle`. |

## Task graph and model

| API | Purpose | Key defaults / notes |
| --- | --- | --- |
| `Operation(module_name, inputs, name=None)` | One forward step in a task graph. | `name` defaults to `module_name`. Inputs may be prior operation names, `'_input_'`, or `(op_name, field_key)` for dict outputs. |
| `Task(name, module_pool, op_sequence, scorer=Scorer(metrics=['accuracy']), loss_func=None, output_func=None)` | Bind modules, a flow, scoring, and loss for one task. | Default loss is `torch.nn.functional.cross_entropy`. Default output is softmax over dim 1. |
| `MultitaskClassifier(tasks, name=None, **kwargs)` | Combine one or more tasks into a shared classifier. | `kwargs` are merged into the classifier config. `device=0` by default; the model stays on CPU if CUDA is unavailable. `dataparallel=True` by default. |
| `MultitaskClassifier.forward(X_dict, task_names)` | Run the requested task flows. | Raises on invalid operation inputs or failed module execution. |
| `MultitaskClassifier.calculate_loss(X_dict, Y_dict)` | Compute per-task loss and active-example counts. | Labels marked `-1` are ignored; 2D label tensors are treated as probabilistic targets. |
| `MultitaskClassifier.predict(dataloader, return_preds=False, remap_labels={})` | Produce golds, probabilities, and optionally predictions. | `return_preds=True` adds `preds`. `remap_labels` can rename or drop dataset label keys. |
| `MultitaskClassifier.score(dataloaders, remap_labels={}, as_dataframe=False)` | Score one or more loaders. | Metric keys are `task/dataset/split/metric`. `as_dataframe=True` returns columns `label`, `dataset`, `split`, `metric`, `score`. |
| `MultitaskClassifier.save(path)` / `load(path)` | Save or restore model weights. | `load` maps tensors to CPU first, then moves to the configured device. |

## Training, logging, and scheduling

| API | Purpose | Key defaults / notes |
| --- | --- | --- |
| `Trainer(name=None, **kwargs)` | Train a `MultitaskClassifier`. | Defaults: `n_epochs=1`, `lr=0.01`, `l2=0.0`, `grad_clip=1.0`, `train_split='train'`, `valid_split='valid'`, `test_split='test'`, `progress_bar=True`, `logging=False`, `checkpointing=False`, `log_writer='tensorboard'`, `optimizer='adam'`, `lr_scheduler='constant'`, `batch_scheduler='shuffled'`. |
| `LogWriter(log_dir='logs', run_name=None)` | JSON-style scalar/text logger. | `run_name` defaults to a date/time path fragment. `cleanup()` writes `log.json`. |
| `TensorBoardWriter(**kwargs)` | TensorBoard-backed logger. | Uses the same directory layout as `LogWriter` and a `SummaryWriter` underneath. |
| `LogManager(counter_unit='epochs', evaluation_freq=1.0)` | Track when to evaluate and checkpoint. | `counter_unit` must be `points`, `batches`, or `epochs`. |
| `Checkpointer(checkpoint_metric='model/all/train/loss:min', checkpoint_factor=1, checkpoint_runway=0, checkpoint_clear=True, checkpoint_task_metrics=None, **kwargs)` | Save and reload the best model seen so far. | Metric format must be `task/dataset/split/metric:mode`, where `mode` is `min` or `max`. |
| `SequentialScheduler` | Yield batches from loaders in order. | Use when batch order should stay deterministic. |
| `ShuffledScheduler` | Yield batches from loaders in shuffled loader order. | Only changes inter-loader batch order; each `DataLoader` still controls its own dataset shuffling. |

### Supported trainer string options
- Optimizers: `sgd`, `adam`, `adamax`
- Learning-rate schedulers: `constant`, `linear`, `exponential`, `step`
- Log writers: `json`, `tensorboard`
- Batch schedulers: `sequential`, `shuffled`

### Learning-rate configuration helpers
- `LRSchedulerConfig`: `warmup_steps=0`, `warmup_unit='batches'`, `warmup_percentage=0.0`, `min_lr=0.0`
- `ExponentialLRSchedulerConfig`: `gamma=0.9`
- `StepLRSchedulerConfig`: `gamma=0.9`, `step_size=5`

## Metrics, utilities, and error analysis

| API | Purpose | Key defaults / notes |
| --- | --- | --- |
| `Scorer(metrics=None, custom_metric_funcs=None, abstain_label=-1)` | Score predictions with one or more metrics. | Standard metrics are filtered to ignore `abstain_label` unless the metric is `coverage`. Custom metric functions may return a float or a dict of metrics. |
| `Scorer.score(golds, preds=None, probs=None)` | Compute the requested metrics. | Raises on empty golds or missing required label arrays. |
| `Scorer.score_slices(S, golds, preds, probs, as_dataframe=False)` | Compute overall and per-slice scores. | `S` must be a NumPy recarray with the same number of rows as `golds`, `preds`, and `probs`. |
| `metric_score(golds=None, preds=None, probs=None, metric='accuracy', filter_dict=None, **kwargs)` | Direct metric helper. | Supported metrics: `accuracy`, `coverage`, `precision`, `recall`, `f1`, `f1_micro`, `f1_macro`, `fbeta`, `matthews_corrcoef`, `roc_auc`. |
| `get_label_buckets(*y)` | Bucket example indices by label tuple. | All label arrays must have the same length. |
| `get_label_instances(bucket, x, *y)` | Select rows from `x` that match a label tuple. | Returns an empty array when the bucket does not exist. |
| `probs_to_preds(probs, tie_break_policy='random', tol=1e-5)` | Convert probability rows to integer predictions. | Requires at least 2 classes. Ties can `random`, `true-random`, or `abstain`. |
| `preds_to_probs(preds, num_classes)` | Convert predicted labels to one-hot probabilities. | Negative labels are rejected. |
| `to_int_label_array(X, flatten_vector=True)` | Normalize labels into integer NumPy arrays. | Rejects non-integer values and can flatten `[n, 1]` arrays to `[n]`. |
| `filter_labels(label_dict, filter_dict)` | Remove aligned examples matching specified labels. | Any example matching any filter criterion is removed from all aligned arrays. |
| `cross_entropy_with_probs(input, target, weight=None, reduction='mean')` | Cross-entropy loss for probabilistic labels. | `input` is logits of shape `[n, num_classes]`; `target` is a probability distribution of the same shape. |

## Useful defaults to remember
- `Scorer` uses `abstain_label=-1`.
- `DictDataset.from_tensors` defaults to `input_data`, `task`, and `SnorkelDataset`.
- `Task` defaults to accuracy scoring, cross-entropy loss, and softmax output.
- `Trainer` defaults to logging off, checkpointing off, and one epoch.
- `Checkpointer` expects the metric string to match the metric key produced by `model.score()`.

## Quick naming rule
If you see a metric or checkpoint key, expect the form:
`task_name / dataset_name / split / metric_name`

If a `:mode` suffix is needed, it belongs only in the checkpoint configuration string.