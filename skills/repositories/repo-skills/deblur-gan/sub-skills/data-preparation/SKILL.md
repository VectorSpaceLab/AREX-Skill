---
name: data-preparation
description: "Prepare paired blur/sharp datasets and explain DeblurGAN
  image-folder layouts."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# data-preparation

Use this sub-skill when the task is about preparing training or inference image folders for DeblurGAN rather than running the model itself.

## What this route covers

- Turning separate blur/sharp folders into paired AB images.
- Explaining the `aligned` and `single` dataset layouts used by the repository.
- Checking supported image extensions and folder naming.
- Understanding why the shipped `unaligned` loader path is not a supported DeblurGAN route.
- Pointing future agents to the safe bundled pair-combination helper.

## Read this when the user asks for

- A training set made from two image trees.
- Help with `trainA` / `trainB` / `testA` / `testB` / `single` style layouts.
- A way to merge blur and sharp images into one AB file.
- A quick explanation of what the loaders expect before training or inference.

## Primary files

- `scripts/combine_pairs.py` — safe, portable pair-concatenation helper.
- `references/data-layout.md` — folder layouts, extension rules, and loader behavior.
- `references/troubleshooting.md` — paired-data and folder-validation failures.

## Workflow summary

1. Decide whether the target is paired training data or single-image inference input.
2. Validate that the input folders contain image files with supported extensions.
3. Use the bundled helper to concatenate A and B images horizontally when paired AB files are needed.
4. Keep the resulting folder layout aligned with the repository's dataset mode:
   - `aligned` expects composite AB images grouped by phase.
   - `single` expects one folder of standalone images.
5. If a request mentions `unaligned`, route it cautiously: the repository contains a loader stub, but it is not initialized by the shipped dataset factory and should not be treated as a supported DeblurGAN workflow.

## Decision points

- If the user already has side-by-side AB images, no extra merge step is needed.
- If the user has separate blur/sharp folders, the bundled helper is the preferred route.
- If the user needs to download example data, keep that as reference-only guidance because the download helper performs network access.
- If the user is trying to use the colorization helper or motion-blur experiments, those belong outside this route.

## Common outputs

- A tree of AB image files for training.
- A single image folder for `model=test` inference.
- A short troubleshooting explanation for missing files, unsupported extensions, or mismatched pair names.

## Cross-links

- Read the root installation reference first if dependencies are missing.
- Read the training sub-skill if the prepared data is meant for optimization.
- Read the inference sub-skill if the prepared data is meant for restoration or evaluation.
