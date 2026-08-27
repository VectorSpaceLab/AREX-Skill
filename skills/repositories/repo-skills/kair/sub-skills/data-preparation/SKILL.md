---
name: data-preparation
description: "Prepare and validate KAIR-compatible image, video, LMDB, and
  meta-info datasets without mutating source data."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# KAIR data preparation

Use this sub-skill when the task is to prepare, inspect, or explain KAIR dataset inputs before training or testing. It covers image folders, paired LQ/GT data, video clip folders, Vimeo90K sequence folders, meta-info files, subimage plans, and LMDB plans.

Do not use this sub-skill for model command ownership. Route image training to `../image-training/SKILL.md`, image inference to `../image-testing/SKILL.md`, and VRT/RVRT model commands to `../video-restoration/SKILL.md`; return here only for dataset layout, meta-info, or conversion questions.

## Safe operating rules

1. Treat KAIR as a source-script checkout: dataset tools in KAIR can be hard-coded and can write, move, copy, or delete data.
2. Prefer the bundled read-only checkers and planners in this sub-skill before any conversion or regrouping.
3. Before recommending a writer, state the expected input tree, output tree, key convention, and whether the operation is destructive or expensive.
4. Never tell the user to run a hard-coded preparation script blindly. If they still want to use one, require a reviewed copy of the data and confirmed paths.
5. Testing datasets for VRT/RVRT normally use frame folders directly; LMDB is mainly for training datasets.

## References

- `references/data-layouts.md` — train/test folder conventions, video layouts, meta-info formats, LMDB structure, and the `dataset_type` mapping.
- `references/data-preparation-workflows.md` — safe plans for DIV2K subimages/LMDBs, REDS, DVD, GoPro, UDM10, DAVIS, Vimeo90K, Set8, and MATLAB-only steps.
- `references/troubleshooting.md` — empty datasets, LQ/GT mismatches, existing output exits, destructive scripts, missing meta-info, LMDB conflicts, libpng fallback, and multiprocessing memory issues.

## Bundled read-only scripts

Run these from any machine with Python 3; they do not import KAIR and do not write data.

```bash
python sub-skills/data-preparation/scripts/check_dataset_layout.py --help
python sub-skills/data-preparation/scripts/check_dataset_layout.py image --root trainsets/trainH
python sub-skills/data-preparation/scripts/check_dataset_layout.py video --root testsets/REDS4/sharp_bicubic --paired-root testsets/REDS4/GT
python sub-skills/data-preparation/scripts/check_dataset_layout.py lmdb --root trainsets/REDS/train_sharp_with_val.lmdb

python sub-skills/data-preparation/scripts/plan_lmdb_conversion.py --dataset div2k
python sub-skills/data-preparation/scripts/plan_lmdb_conversion.py --dataset reds
```

## Quick routing

- "Create a DIV2K LMDB" → use `references/data-preparation-workflows.md#div2k-subimages-and-lmdbs`, then `scripts/plan_lmdb_conversion.py --dataset div2k`.
- "Check REDS layout for VRT" → use `references/data-layouts.md#video-folder-layouts` and `scripts/check_dataset_layout.py video` on both LQ and GT roots.
- "Why no dataset found?" → use `references/troubleshooting.md#empty-dataset-or-no-images-found` and check folder depth, extensions, and `folder_lq`/`folder_gt` pairing.
- "Prepare GoPro as video" → use `references/data-preparation-workflows.md#gopro-video-deblurring-layout`; warn that the original regrouping script moves folders and deletes the original `train`/`test` folders.
- "List KAIR dataset_type values" → use `references/data-layouts.md#dataset_type-mapping`.
