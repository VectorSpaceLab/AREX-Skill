---
name: data-and-training
description: "Prepares AnyDoor datasets, preprocessing, training, and weight conversion."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Data and Training

Use this sub-skill when the task is about AnyDoor dataset layout, preprocessing,
debugging data samples, starting training, or converting initialization
weights.

## What this sub-skill owns

- Dataset path validation and dataset-family conventions.
- UVO annotation reorganization.
- Training recipe and resource planning.
- Data-debug sampling and visualization.
- Stable Diffusion 2.1 to AnyDoor-style weight conversion guardrails.

## What this sub-skill does not own

- Generation workflows and mask validation for inference.
- Environment installation and checkpoint patching.
- Demo launch or Cog prediction details.

Route those to the sibling sub-skills.

## Read first

- `../../references/overview.md`
- `../../references/checkpoints-and-configs.md`
- `../../references/troubleshooting.md`
- `references/dataset-formats.md`
- `references/training-workflows.md`
- `references/model-architecture.md`
- `references/troubleshooting.md`

## Use these scripts

- `scripts/check_dataset_config.py` to inspect `datasets.yaml`-style layouts.
- `scripts/rewrite_uvo_annotations.py` to convert UVO annotations into the repo’s
  expected map format.
- `scripts/convert_control_init.py` to validate the SD2.1 conversion workflow.
- `scripts/run_train_checked.sh` to print or run the training command after
  validating the setup.

## Trigger phrases

This is usually the right branch when the user says things like:

- “How should I structure my dataset?”
- “Why does the data loader fail?”
- “How do I process UVO annotations?”
- “What does run_dataset_debug do?”
- “How do I start training?”
- “How do I convert the SD2.1 checkpoint?”
- “What datasets does AnyDoor mix during training?”

## Input contract

The data side of AnyDoor expects user-provided roots for things like:

- YouTube-VOS / YouTube-VIS image and annotation trees,
- VIPSeg panoptic masks,
- UVO sparse videos and JSON mappings,
- MOSE image and annotation roots,
- MVImageNet text/index files and image trees,
- VITON-HD, DressCode, FashionTryon, SAM, Saliency, and LVIS-style layouts.

The exact path keys live in `configs/datasets.yaml`.

## Output contract

A successful data/training route should explain:

- which dataset family the user is preparing,
- what file layout that family expects,
- which labels or annotation conventions matter,
- what can be validated safely without loading the entire dataset,
- and whether the task is a quick config check or a long-running training path.

## Default workflow order

1. Verify the dataset config structure.
2. Confirm the file layout and label conventions for the chosen dataset family.
3. Run a small preprocessing or debug helper if needed.
4. Only then consider training or weight conversion.

## Common decisions

- **Dataset paths still contain placeholders**: stop and patch them first.
- **UVO annotation layout is raw**: run the rewriter before training.
- **Need a quick sanity check only**: use the dataset config checker instead of a
  full dataloader.
- **Training requested without checkpoints**: explain the initialization and
  resource requirements first.
- **Conversion requested**: point out the source script’s stale config path and
  use the bundled guardrail script.

## Troubleshooting focus

This branch owns symptoms such as:

- placeholder dataset roots,
- wrong foreground labels in parse masks,
- missing `pycocotools`, `lvis`, or `panopticapi`,
- dataset loaders that work only on real data and therefore need safe config
  checks first,
- Lightning/DDP issues,
- and the source weight-conversion helper’s path bug.

## Handy reminders

- The training recipe is multi-dataset and GPU-oriented.
- `BaseDataset.process_pairs` produces the `ref`, `jpg`, `hint`, `extra_sizes`,
  and crop metadata that the inference side also relies on.
- Several dataset families use different foreground labels in parse masks.
- Full training is much heavier than a config or import check.

## Cross-links

When the issue is really about setup or checkpoints, route back to
`setup-and-checkpoints`.
When the issue is really about generation or the demo, route to
`inference-and-demo`.

## Quality bar

A future agent should be able to prepare AnyDoor data, explain the relevant
annotations, and distinguish between a safe config validation and a heavy
training run without reopening the source repository.
