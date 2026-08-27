# Training workflows

This reference covers the trainer classes and the shared hook/logging machinery that ties them into a complete training loop.

## Trainer map

| Trainer | Best for | Key requirements |
| --- | --- | --- |
| `MetricLossOnly` | A trunk + optional embedder trained only with a metric loss | `models={"trunk": ...}` and `loss_funcs={"metric_loss": ...}` |
| `TrainWithClassifier` | A trunk + embedder + classifier setup that mixes metric and classification losses | `models` needs `trunk` and `classifier`; `loss_funcs` needs `metric_loss` and `classifier_loss` |
| `CascadedEmbeddings` | Multiple sub-embeddings trained from a single embedder output | Requires `embedding_sizes` and stage-specific `loss_funcs`, `miners`, and optional classifiers |
| `DeepAdversarialMetricLearning` | Adversarial generator training with metric and synthetic losses | Needs `trunk`, `generator`, `metric_loss`, `g_adv_loss`, and `synth_loss`; can also use `classifier_loss` |
| `TwoStreamMetricLoss` | Anchor / positive-negative two-stream datasets | Dataset must return `(anchor, positive, label)`; only tuple miners are supported |

## Shared trainer arguments

All trainer subclasses inherit the same base argument pattern from `BaseTrainer`.

Important shared fields:

- `models`: at minimum `{"trunk": trunk_model}`.
- `optimizers`: keys usually end in `_optimizer`.
- `batch_size`: per-iteration batch size.
- `loss_funcs`: at minimum `{"metric_loss": loss_func}`.
- `dataset`: the training dataset, not the validation set.
- `mining_funcs`: optional `subset_batch_miner` and `tuple_miner` entries.
- `iterations_per_epoch`: useful when sampler-driven epochs are not naturally sized.
- `data_device` and `dtype`: move input batches to the correct device and precision.
- `loss_weights`: weight the named losses before summing.
- `sampler` or `batch_sampler`: controls how batches are formed.
- `freeze_these`: freeze named models or losses during training.
- `freeze_trunk_batchnorm`: keep trunk batchnorm layers in eval mode.
- `label_hierarchy_level`: select which label level to use when labels are hierarchical.
- `data_and_label_getter`: adapt datasets that do not return `(data, label)` directly.
- `dataset_labels` and `set_min_label_to_zero`: remap labels into rank order when needed.
- `end_of_iteration_hook` and `end_of_epoch_hook`: logging, validation, and checkpoint hooks.

## Hook and logging flow

`logging_presets.HookContainer` is the main bundled helper for end-to-end training runs.

Typical sequence:

1. Build a record keeper with `logging_presets.get_record_keeper(...)`.
2. Create a `HookContainer` with a chosen `primary_metric`.
3. Create a tester and pass `hooks.end_of_testing_hook` into it.
4. Create the trainer with `hooks.end_of_iteration_hook` and the `end_of_epoch_hook` returned by `hooks.end_of_epoch_hook(...)`.
5. Train.
6. Query `hooks.get_loss_history()` and `hooks.get_accuracy_history(...)` after the run.

Important `HookContainer` details:

- The default `primary_metric` is `mean_average_precision_at_r`.
- `validation_split_name` defaults to `val`.
- `end_of_epoch_hook` can perform validation every `test_interval` epochs and stop early when `patience` is exceeded.
- `primary_metric` must be one of `mean_average_precision_at_r`, `r_precision`, `precision_at_1`, or `NMI`.

## Distributed wrappers

`DistributedLossWrapper` and `DistributedMinerWrapper` wrap a loss or miner for `torch.distributed` training.

- They are useful when the current batch should interact with gathered embeddings from other ranks.
- `efficient=True` reduces memory and changes the exact gradient path.
- `CrossBatchMemory` is not supported with `efficient=True` in the distributed loss wrapper.
- The wrappers only make sense when a distributed process group is actually initialized.

Treat these wrappers as optional advanced support unless the user explicitly asks for distributed training.

## Useful trainer debug patterns

- Start with a tiny `EmbeddingDataset` or a tiny fake dataset before moving to real data.
- Use `MPerClassSampler` when the chosen loss needs positive pairs or triplets in each batch.
- If a trainer immediately fails schema checks, inspect the key names in `models`, `loss_funcs`, `mining_funcs`, `optimizers`, and `lr_schedulers`.
- If the validation metric never changes, confirm that the end-of-epoch hook is actually calling the tester and that the validation split exists.

## Cross-check against the tests

Useful native references for this layer include:

- `tests/trainers/test_key_checking.py`
- `tests/trainers/test_metric_loss_only.py`
- `tests/utils/test_distributed.py`
- `tests/testers/test_global_embedding_space_tester.py`
- `tests/testers/test_with_same_parent_label_tester.py`
