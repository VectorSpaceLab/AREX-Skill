---
id: data-preparation
name: data-preparation
description: "Prepare, inspect, validate, and troubleshoot PointCNN
  classification and segmentation datasets, HDF5 files, file lists, labels,
  splits, and PLY artifacts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PointCNN data preparation

Use this sub-skill when a PointCNN workflow needs a dataset layout, a
classification or segmentation HDF5 contract, a file-list check, or a small
PLY/HDF5 inspection. This is a read-only preparation boundary: it does not
train, evaluate, download, unpack, convert, write PLY output, or alter a cache.

## Route first

- **Classification inputs:** use `classification-workflows` after selecting
  one of the six classification dataset cards below. Classification HDF5
  entries follow the legacy basename lookup rule.
- **Segmentation inputs:** use `segmentation-workflows` after validating a flat
  or nested segmentation list. `data_num` and `label_seg` describe active
  points; `label` is usually a sample or room placeholder.
- **Model/backend issues:** use `core-xconv-and-operators` for operator and
  TensorFlow diagnostics. Use `segmentation-workflows` for FPS readiness and
  prediction merging, and `evaluation-and-artifacts` for metrics and outputs.
- **Input failures:** read [troubleshooting.md](references/troubleshooting.md)
  and then run the bundled read-only tools. Do not repair an HDF5 file in
  place.

The dataset-specific contract is in
[dataset-matrix.md](references/dataset-matrix.md). Read
[hdf5-and-filelist-schemas.md](references/hdf5-and-filelist-schemas.md) before
creating or editing a list.

## Safe validation sequence

Run these commands from the installed self-contained PointCNN skill root; never rely on a default data directory:

```bash
python3 sub-skills/data-preparation/scripts/inspect_filelists.py --help
python3 sub-skills/data-preparation/scripts/inspect_filelists.py \
  --list /path/to/data/train_files.txt --kind classification --check-h5

python3 sub-skills/data-preparation/scripts/validate_pointcnn_h5.py --help
python3 sub-skills/data-preparation/scripts/validate_pointcnn_h5.py \
  --filelist /path/to/data/train_files.txt --kind classification
python3 sub-skills/data-preparation/scripts/validate_pointcnn_h5.py \
  --filelist /path/to/data/train_files.txt --kind segmentation
python3 sub-skills/data-preparation/scripts/validate_pointcnn_h5.py --self-test
python3 sub-skills/data-preparation/scripts/inspect_filelists.py --self-test
```

The validator checks required keys, ranks, floating/integer dtypes, finite
values, aligned sample and point dimensions, `data_num` bounds, active label
ranges, and optional reconstruction indices. Give it `--class-count` when a
selected setting supplies a class/part count. Give it `--index-size` for a
one-dimensional source bound (or the point-id column of a pair),
`--index-group-count` for a pair's room bound, or `--room-sizes` for exact
ScanNet-style `(room, point)` bounds. Without source sizes it still checks
nonnegative active indices and reports that the external source bound remains
unproved.

Both tools are read-only for user paths. `--self-test` uses a temporary fixture
only; it does not touch a dataset. The file-list inspector resolves every entry
relative to the list that contains it and reports the actual resolved path.
For classification it deliberately applies the legacy `basename()` behavior;
for segmentation child lists it resolves each child entry relative to that
child list.

## Input contracts to hand off

Before routing onward, record:

1. dataset and task, raw/conversion status, and train/validation/test split;
2. exact list paths and whether a segmentation training list is nested;
3. HDF5 feature width, point padding width, class or part count, and label map;
4. whether `indices_split_to_full` is absent, one-dimensional, or ScanNet-style
   two-dimensional, plus the source bounds used for validation; and
5. whether any PLY visualization or conversion marker is only partial.

Classification HDF5 contains `data[B,N,C]`, `label[B]` or `[B,1]`, and may have
`normal[B,N,3]`; the loader concatenates `normal` to `data`. Segmentation HDF5
contains `data[B,N,C]`, `data_num[B]`, `label[B]` or `[B,1]`, and
`label_seg[B,N]`, with optional `indices_split_to_full[B,N]` or `[B,N,2]`.
Only the prefix `:data_num[i]` is real data. Keep all files in one list on one
schema and index convention.

## Dataset and side-effect boundary

The supported classification routes are **ModelNet40**, **ScanNet object
classification**, **TU-Berlin**, **MNIST**, **CIFAR-10**, and **Quick Draw**.
The supported segmentation routes are **ShapeNet Parts**, **S3DIS**, **ScanNet
segmentation**, and **Semantic3D**. The matrix records each raw layout,
conversion output, split, label convention, and feature normalization.

Acquisition and conversion are not safe smoke tests. Network download, archive
extraction, mutable file moves, HDF5 generation, PLY generation, and cache
markers require an explicit destination and approval. In particular, the
Semantic3D acquisition/decompression path is a documented approximately
900-GB operation and must never be a default or bundled runnable action.
S3DIS `.labels`/`.dataset` and Semantic3D `.unpacked` markers are hints only:
a marker can survive a partial conversion or extraction. Inspect actual files
and validate representative HDF5 files before trusting a marker.

This codebase is legacy TensorFlow 1.x graph-mode software. HDF5 validation is
framework-independent and does not establish model readiness. The current
runtime evidence is: TensorFlow 1.15 import and device discovery passed, while
a GPU/custom-op session timed out. Farthest-point sampling (FPS) is therefore
`BLOCKED_REQUIRED_BACKEND`, never passed. Do not claim a segmentation run from
an input-only or CPU validation result.

## PLY handling

PLY helpers are diagnostic writers, not input preparation. They expect points
`[N,3]`; optional normals and colors are parallel arrays. Batch helpers truncate
samples to `data_num`, while property helpers map zero to black and use a
positive property maximum. The legacy writer creates parent directories and
writes binary vertex PLY, so keep any approved visualization in a new output
root and inspect one tiny file before scaling up. The bundled tools never write
PLY.

## Files in this sub-skill

- [dataset-matrix.md](references/dataset-matrix.md): dataset layouts,
  conversions, labels, splits, feature conventions, and side-effect limits.
- [hdf5-and-filelist-schemas.md](references/hdf5-and-filelist-schemas.md):
  HDF5 keys/ranks/dtypes, list resolution, `data_num`, indices, and PLY API
  contracts.
- [troubleshooting.md](references/troubleshooting.md): safe diagnosis and
  recovery order.
- [validate_pointcnn_h5.py](scripts/validate_pointcnn_h5.py): read-only HDF5
  contract validator with optional source-index bounds.
- [inspect_filelists.py](scripts/inspect_filelists.py): read-only flat/nested
  list resolver and optional HDF5 checker.
