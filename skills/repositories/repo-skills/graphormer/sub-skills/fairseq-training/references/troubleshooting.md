# Troubleshooting

Use this guide when a Graphormer training command does not look safe to run or
when a recipe fails before the first training step.

## Missing `--user-dir` or wrong registry state

Symptoms:
- `--arch graphormer_base` is rejected
- `--task graph_prediction` or `--task is2re` is missing
- a model or criterion name is not visible in fairseq

Fixes:
- ensure the Graphormer user-dir package is imported before invoking fairseq
- point `--user-dir` at the directory containing `models/`, `tasks/`, and
  `criterions/`
- rerun the registry checker in a fresh process

## Dataset download or layout failures

Symptoms:
- ZINC, PCQM4M, MolHIV, or OC20 data never appears
- the command starts but fails while loading dataset paths
- a recipe assumes a dataset split that is not present locally

Fixes:
- confirm the dataset source and name before training
- for custom data, use the dataset sub-skill to validate the module first
- treat OGB/OC20 downloads as external prerequisites, not part of the command

## `num_classes` and target-shape mismatches

Symptoms:
- `Must set task.num_classes`
- the loss fails because targets and predictions have different dimensions

Fixes:
- set `--num-classes 1` for scalar regression and binary classification
- use the class count expected by the dataset for multiclass tasks
- keep the loss family consistent with the task and output head

## fp16 or CUDA problems

Symptoms:
- the command fails on a CPU-only host
- mixed precision creates NaNs or overflow
- OOM errors appear during the first forward/backward pass

Fixes:
- use a CUDA-capable environment for the historical recipes
- reduce batch size first, then increase update frequency if needed
- keep the command renderer and smoke checker separate from the full run

## OC20 / IS2RE memory pressure

Symptoms:
- the historical OC20 batch size is too large for the GPU
- the run fails before the first validation step

Fixes:
- start with the documented small batch size and reduce further if needed
- use the notes in the workflow reference before trying a real run
- consider a later Researcher session if the memory budget is not available

## Pretrained checkpoint confusion

Symptoms:
- a fine-tuning command loads the wrong checkpoint family
- the output layer does not match the target task

Fixes:
- check whether the workflow is pure evaluation or fine-tuning
- keep `--load-pretrained-model-output-layer` only when the head is supposed to
  match the target task
- use the pretrained/evaluation sub-skill for checkpoint-specific guidance

## Command-builder expectations

Symptoms:
- the helper prints a command that is not exactly what you expected
- the helper is used as if it launches training

Fixes:
- remember that the helper only renders a shell command
- edit the rendered command manually for additional tuning if needed
- use the helper's output as a reviewable starting point, not as an executor
