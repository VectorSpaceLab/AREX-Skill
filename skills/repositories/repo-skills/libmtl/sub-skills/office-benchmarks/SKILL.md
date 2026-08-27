---
name: office-benchmarks
description: "Routes LibMTL's Office-31 and Office-Home multi-input
  classification workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# office-benchmarks

Use this sub-skill for the Office-31 and Office-Home benchmark workflows.

## Covers

- Office-31 multi-input classification.
- Office-Home multi-input classification.
- The bundled office split layout and dataloader recipe.
- A self-contained Office runtime package under `scripts/office_runtime/`.
- An unpackaged launcher at `scripts/main.py` plus the install entry point
  `scripts/install_office_runtime.py`.
- ResNet-18 based encoders and task-specific linear decoders.

## Does not cover

- NYUv2 or Cityscapes dense prediction.
- QM9 graph regression.
- PAWS-X multilingual text classification.
- Core API or custom method development unless the question is specifically
  about the office benchmark wiring.

## When to use this sub-skill

Choose this route when the user asks things like:

- "How do I train Office-31?"
- "What is the Office-Home layout?"
- "Why must `multi_input` be true here?"
- "How do the office dataloaders map tasks to domains?"
- "How do I validate the split files?"

## Read next

- `../../references/configuration.md` for the shared flags and method kwargs.
- `../../references/troubleshooting.md` for cross-cutting install and runtime
  failures.
- `references/workflows.md` for the command pattern.
- `references/task-contracts.md` for the task dictionary, loader, and
  encoder/decoder shapes.
- `references/data-layouts.md` for the expected split and image trees.
- `references/troubleshooting.md` for office-specific failures.

## Workflow

1. Confirm the dataset family: `office-31` or `office-home`.
2. Confirm that the user expects multi-input classification.
3. Validate the split text files and the image root.
4. Run `scripts/check_office_data.py` to confirm the bundled split files and
   image root before training.
5. Install the self-contained runtime package with
   `scripts/install_office_runtime.py` when you need the console entry point.
6. Launch the benchmark through `scripts/main.py` or the installed
   `libmtl-office` entry point, not through an external checkout.
7. Allow the pretrained `resnet18` backbone to download or use cache.

## Critical constraints

- `multi_input` must be `True`.
- The bundled runtime builds one dataloader per domain/task from its own split
  files.
- The task list depends on the dataset family:
  - Office-31: `amazon`, `dslr`, `webcam`
  - Office-Home: `Art`, `Clipart`, `Product`, `Real_World`

## Exit criteria

Leave this sub-skill when the user has the correct dataset family, split files,
run command, and failure-recovery notes for the office benchmark.
