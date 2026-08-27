---
name: vision-benchmarks
description: "Routes LibMTL's NYUv2 and Cityscapes vision benchmark workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# vision-benchmarks

Use this sub-skill for the NYUv2 and Cityscapes image benchmark workflows.

## Covers

- NYUv2 single-input dense prediction.
- Cityscapes single-input dense prediction.
- DeepLabV3+ with `resnet_dilated` and `DeepLabHead`.
- SegNet+MTAN for the NYUv2 variant.
- The shared NYUv2 helper modules for metrics, ASPP heads, SegNet+MTAN, and
  data loading.

## Does not cover

- Office-31 / Office-Home multi-input classification.
- QM9 graph regression or PAWS-X text classification.
- Core `Trainer` or extensibility questions that do not depend on the vision
  benchmark layout.

## When to use this sub-skill

Choose this route when the user asks things like:

- "How do I train NYUv2?"
- "What is the Cityscapes data layout?"
- "How do I use the SegNet+MTAN variant?"
- "What does the NYUv2 `task_dict` look like?"
- "Why is `multi_input` false for these examples?"

## Read next

- `../../references/configuration.md` for the shared flags and architecture
  kwargs.
- `../../references/troubleshooting.md` for cross-cutting install and runtime
  failures.
- `references/workflows.md` for the benchmark recipes.
- `references/task-contracts.md` for the task dictionaries, losses, metrics,
  and output-channel expectations.
- `references/data-layouts.md` for the expected preprocessed data trees.
- `references/troubleshooting.md` for vision-specific failures.

## Workflow

1. Confirm the dataset: NYUv2 or Cityscapes.
2. Confirm the architecture family: DeepLabV3+ or SegNet+MTAN.
3. Verify the preprocessed `npy` directory layout.
4. Confirm the example is being run from the correct example directory.
5. Run `scripts/check_vision_data.py` to validate the bundled preprocessed
   layout before training.
6. Check that CUDA and pretrained-weight downloads are available.

## Critical constraints

- Both benchmarks are single-input problems, so `multi_input` must be `False`.
- NYUv2 uses three tasks: segmentation, depth, and surface normal.
- Cityscapes uses two tasks: segmentation and depth.
- The Cityscapes workflow reuses the NYU helper modules by adding the
  sibling directory to `sys.path`.

## Exit criteria

Leave this sub-skill when the user has a complete command, data layout, and
failure-recovery story for the selected vision benchmark.
