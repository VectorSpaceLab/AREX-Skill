---
name: prompted_multitask_training
description: Execute a deterministic minimal optimizer step on prompted multitask text examples and log loss/parameter changes.
---

# Prompted Multitask Training Step

Use this skill for bounded recovery of the T0/P3 mechanism when full encoder-decoder fine-tuning is not feasible. It provides a small softmax classifier over bag-of-words features so an experiment can prove that prompted examples are consumed by a real parameter update.

## Inputs
- Rendered training records with `source` text and `target` labels.
- Label vocabulary and optional learning rate/epoch count.

## Outputs
- Parameters before and after training, loss before/after, and a prediction helper.

## Workflow
1. Build a deterministic vocabulary from source-task prompted text.
2. Initialize label weights to zero for reproducibility.
3. Compute multiclass logistic loss and gradients.
4. Apply gradient descent updates and log parameter changes.

## Validation
Run the included tests. Recovery should save `training_trace.json` with `params_before` and `params_after`.

## Limitations
This is a declared proxy for supervised prompted fine-tuning, not a replacement for T5/T0 model training.
