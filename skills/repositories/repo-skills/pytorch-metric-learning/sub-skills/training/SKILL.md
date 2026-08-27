---
name: training
description: "Routes PyTorch Metric Learning questions about trainers, hooks,
  logging, checkpointing, and optional distributed wrappers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training

Use this sub-skill when the user wants to wire PyTorch Metric Learning into an actual training loop, validation hook, or checkpoint/logging workflow.

## Typical triggers

- "How do I use MetricLossOnly / TrainWithClassifier / CascadedEmbeddings / DeepAdversarialMetricLearning / TwoStreamMetricLoss?"
- "How do I configure the trainer dictionary keys?"
- "How do I add logging, early stopping, or checkpoint saving?"
- "How do I freeze part of the model or use `MPerClassSampler` during training?"
- "How do I wrap a loss or miner for distributed training?"

## In scope

- Trainers: `BaseTrainer`, `MetricLossOnly`, `TrainWithClassifier`, `CascadedEmbeddings`, `DeepAdversarialMetricLearning`, `TwoStreamMetricLoss`.
- Hooking and logging: `logging_presets.HookContainer`, record-keeper integration, model saving/loading, early stopping, validation hooks, and metric history access.
- Trainer configuration: `models`, `optimizers`, `loss_funcs`, `mining_funcs`, `sampler`, `batch_size`, `iterations_per_epoch`, `freeze_these`, `freeze_trunk_batchnorm`, `label_hierarchy_level`, `data_and_label_getter`, `dataset_labels`, `set_min_label_to_zero`, `lr_schedulers`, and `gradient_clippers`.
- Optional distributed wrappers: `DistributedLossWrapper` and `DistributedMinerWrapper`.

## Out of scope

- Choosing the loss/miner/distance/reducer/regularizer stack belongs in `components`.
- Accuracy calculators, testers, and nearest-neighbor search belong in `evaluation`.
- Downloading datasets or building samplers belongs in `data` unless the question is purely about their role inside a trainer.

## How to use this sub-skill

1. Read `references/training-workflows.md` for the trainer map, hook sequence, and config expectations.
2. Run `scripts/smoke_training.py` when you want to confirm the trainer wiring on toy data without downloads.
3. Read `references/troubleshooting.md` when the failure mentions missing dictionary keys, frozen modules, checkpointing, or logging dependencies.
4. If the request mentions distributed loss/miner wrappers, read the optional distributed note in the workflow reference and treat GPU execution as optional unless the user specifically asks for it.

## Common routing decisions

- If the user only needs the right loss or miner, route to `components` first.
- If the user wants retrieval metrics, validation scores, or nearest-neighbor search after training, route to `evaluation` after the trainer is set up.
- If the user wants dataset download or batch construction help, route to `data` before wiring the trainer.

## Useful public facts

- All trainer subclasses share the `BaseTrainer` argument pattern.
- `MetricLossOnly` needs a trunk model and a `metric_loss` entry.
- `TrainWithClassifier` expects a trunk/classifier architecture and both metric and classification losses.
- `CascadedEmbeddings` splits the embedding dimension into multiple stages.
- `DeepAdversarialMetricLearning` adds generator-specific loss keys and epoch scheduling.
- `TwoStreamMetricLoss` expects a dataset that yields `(anchor, positive, label)`.
- `HookContainer` is the easiest path for record-keeper, tensorboard, early stopping, and model checkpointing.

## Read next

- `references/training-workflows.md` for trainer and hook details.
- `references/troubleshooting.md` for trainer-key, checkpoint, logging, and distributed-wrapper failures.
- `scripts/smoke_training.py` for a tiny end-to-end trainer smoke check.
