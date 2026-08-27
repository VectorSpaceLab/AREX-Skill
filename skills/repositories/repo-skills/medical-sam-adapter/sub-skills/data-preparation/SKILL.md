---
name: data-preparation
description: "Prepare Medical-SAM-Adapter data, checkpoints, and CUDA
  prerequisites, then validate a registered 2D or 3D sample contract before
  training or evaluation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# Data preparation

Use this route when a Medical-SAM-Adapter run has uncertain input files,
registered dataset name, sample shape, prompt metadata, checkpoint, dependency,
or GPU/memory requirements. This route is a read-only preflight: it never
downloads data or weights, edits a dataset, imports the repository to inspect a
sample, or launches training/evaluation.

Start at the [root Medical-SAM-Adapter route](../../SKILL.md) when the user has
not chosen a workflow. After the inputs pass this route, hand model and command
choices to [training](../training/SKILL.md), or hand checkpoint scoring and
metric questions to [evaluation](../evaluation/SKILL.md). Do not use this route
for the standalone detector workflow; that belongs to
[MobileSAMv2 inference](../mobile-inference/SKILL.md).

## Required preflight sequence

1. **Freeze the caller-owned paths.** Record `data_path`, checkpoint paths,
   output paths, and the selected CUDA device explicitly. A path is ready only
   when the expected file or directory is readable. Do not infer a data root
   from a checkpoint filename or from the current working directory.
2. **Choose the exact dispatcher spelling.** The source compares names literally:
   `isic`, `decathlon`, `REFUGE`, `LIDC`, `DDTI`, `Brat`, `STARE`, `kits`,
   `WBC`, `segrap`, `toothfairy`, `atlas`, `pendal`, and `lnq`. Read
   [dataset layouts](references/dataset-layouts.md); changing case changes the
   branch or produces an unsupported-dataset path.
3. **Check the adapter layout before opening a loader.** Confirm the required
   CSV, image/mask pair, volume, NRRD, NumPy, pickle, or MONAI split files for
   one representative case. Missing files, an unmatched stem, or a missing
   rater is a data error, not a reason to substitute a different registry name.
4. **Check the runtime gate.** Actual training and evaluation require a
   CUDA-capable PyTorch runtime. Verify CUDA availability, the selected device,
   one CUDA allocation, `python -m pip check`, and the dependency for the
   selected adapter. CPU parsing or metadata validation is diagnostic only; it
   does not verify the workflow. See
   [checkpoints and environment](references/checkpoints-and-environment.md).
5. **Check checkpoint roles without deserializing untrusted files.**
   `-sam_ckpt` is the base SAM-family input for checkpoint-consuming builders;
   `-weights` is a saved adapter/resume record. Both must be explicit readable
   files and must match the selected network and encoder. Never download a
   missing file or treat a basename as compatibility evidence.
6. **Export one sample declaration and validate it.** From the installed skill
   root, run the bundled read-only helper:

   ```bash
   python sub-skills/data-preparation/scripts/validate_sample_contract.py \
     --sample sample.json --format auto --dataset isic
   ```

   Use `--help` for the JSON/NPZ schema. A nonzero status blocks the run. A zero
   status proves only declared fields, ranks, channel/depth relationships,
   prompt coordinates, and optional chunk bounds; it does not decode NIfTI/NRRD,
   run MONAI transforms, load a checkpoint, or execute CUDA.
7. **Apply dimensional and mask checks.** A per-sample image is `[C,H,W]` for
   2D or `[C,H,W,D]` for 3D; `DataLoader` adds `[B,...]` later. The label has
   the same rank and corresponding spatial axes. The source permits H/W to be
   resized separately to `image_size` and `out_size`, but depth and slice
   alignment must never change. Follow [the data contract](references/data-contract.md).
8. **Choose memory controls before launch.** For 2D lower `-b` and
   `-image_size`. For MONAI 3D lower `-b`, `-chunk`, `-num_sample`, and
   evaluation `-evl_chunk`; keep `-roi_size` compatible with the transformed
   in-plane data. Then route to training or evaluation rather than launching
   from this skill.

## Sample contract at a glance

A custom dataset item must provide:

```text
{
    "image": numeric [C,H,W] or [C,H,W,D],
    "label": numeric mask with the same rank and aligned spatial axes,
    "p_label": 0/1 prompt label(s),
    "pt": [x,y], [N,2], or one [x,y] point per 3D slice,
    "image_meta_dict": {"filename_or_obj": "stable-case-name"}  # recommended
}
```

The README calls `image_meta_dict` optional, but the current training and
validation loops access `filename_or_obj` while naming visualizations. Include
it for the unmodified core path. `box` and `multi_rater` are optional adapter
fields; the core prompt call passes `boxes=None`, so neither replaces the
required `label`/`pt` contract.

For 2D built-in adapters, images are normally RGB `[3,H,W]`; REFUGE returns two
mask channels in cup-then-disc order. Direct 3D adapters normally return
`[1,H,W,D]` image and mask; the 3D loop generates one prompt per depth slice and
repeats image slices to three channels before SAM. MONAI Decathlon/BTCV data is
loaded channel-first and transformed before the crop/chunk checks. Empty masks
may produce a negative prompt label (`0`) and a fallback point; inspect that
case instead of silently treating it as a valid foreground annotation.

`-multimask_output` is a decoder output/class-count setting, not a way to create
missing labels. The original SAM branch requests multiple masks when its value
is greater than one; EfficientSAM and MobileSAM branches force a single output.
Keep it aligned with label channels and route the model decision to training.

## Scope boundary and limits

This route owns data layouts, exact registry names, custom sample fields,
prompt/mask shape preflight, checkpoint/environment prerequisites, and memory
risk. It does not own optimizer/adaptation internals, metric formulas, or
standalone object-aware detector operation. Concrete failures and source-level
limits are collected in [troubleshooting](references/troubleshooting.md).
