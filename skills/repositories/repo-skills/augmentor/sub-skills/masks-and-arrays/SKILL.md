---
name: masks-and-arrays
description: "Mask-safe ground truth augmentation and in-memory grouped array
  workflows for Augmentor."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Masks and Arrays

Use this sub-skill when the task needs Augmentor to apply identical random transforms to an original image and its mask/ground-truth companions, especially segmentation or multi-mask data.

## Route here for

- Directory-backed `Pipeline.ground_truth(ground_truth_directory)` workflows where original images and ground-truth images must be matched before `sample()`.
- Verifying `get_ground_truth_paths()` pairs before running a mask-safe disk pipeline.
- In-memory `DataPipeline(images, labels=None)` workflows where each sample is a grouped list such as `[image_array, mask_array]` or `[image_array, mask1_array, mask2_array]`.
- `DataPipeline.sample(n)` and `DataPipeline.generator(batch_size=1)` return-shape questions, with optional labels preserved alongside grouped arrays.

## Route elsewhere

- Generic directory scanning, output locations, `sample()`/`process()` to disk, seeding, and multithreading: use the sibling `pipeline-augmentation` sub-skill.
- Operation selection, probability semantics, and detailed parameter ranges: use the sibling `operation-reference` sub-skill.
- Keras, PyTorch, DataFrame, and non-mask generator integrations: use the sibling `generators-and-frameworks` sub-skill.

## Fast workflow

1. Choose the data path:
   - Use `Pipeline.ground_truth()` for original and mask images already stored on disk with matching filenames and, for class data, matching class subfolders.
   - Use `DataPipeline` for arrays already in memory or for original plus one or more masks per sample.
2. Confirm shapes before augmentation. Directory ground-truth images should match original image dimensions; `DataPipeline` groups may mix channel counts, but each array must be convertible by Pillow.
3. Add only operations that are valid for every member of each group. Geometric transforms are the usual mask-safe choice; color-only changes may not make sense for label masks.
4. Inspect a tiny sample before scaling up.

## Bundled references and helper

- [Mask workflows](references/mask-workflows.md) covers directory ground-truth pairing, class subfolders, and `get_ground_truth_paths()`.
- [Data formats](references/data-formats.md) covers `DataPipeline` group/list semantics, labels, `sample()`, and `generator()`.
- [Troubleshooting](references/troubleshooting.md) covers common no-match, shape, label, and no-mask pitfalls.
- [Array smoke helper](scripts/augmentor_mask_array_smoke.py) runs a synthetic in-memory original+mask check with NumPy arrays only.
