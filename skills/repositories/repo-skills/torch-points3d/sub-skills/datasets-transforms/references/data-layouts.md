# Data Layouts and Dataset Families

## Purpose

Read this before pointing Torch Points3D at local point-cloud datasets or
running dataset constructors that may download, preprocess, or rewrite files.

## General layout rules

- `BaseDataset` derives a default data path from `dataset_opt.dataroot` and either `dataset_name` or the dataset class name with `Dataset` removed and lowercased.
- Data configs often expect `dataroot: data`; command-line overrides should point to a project-specific data root.
- Many public datasets are large and governed by licenses or terms. Do not trigger downloads until the user approves size, credentials, and destination.
- Preprocessing transforms can cache processed files through PyG `InMemoryDataset`; use scratch copies or known-safe roots for experiments.

## Dataset family summary

| Task | Common configs | Dataset classes | Notes |
| --- | --- | --- | --- |
| Segmentation | `shapenet`, `shapenet-fixed`, `s3dis1x1`, `s3disfused`, `scannet`, `semanticKitti` | `ShapeNetDataset`, `S3DIS1x1Dataset`, `S3DISFusedDataset`, `ScannetDataset`, `SemanticKittiDataset` | ShapeNet is a fast prototyping target; ScanNet/S3DIS/SemanticKITTI need real dataset layouts. |
| Classification | `modelnet` | `ModelNetDataset` | ModelNet10/40 family via PyG-style dataset wrappers. |
| Object detection | `scannet`, `scannet-fixed`, `scannet-sparse` | `ScannetDataset` | VoteNet-style configs and box labels. |
| Panoptic | `s3disfused`, `scannet-sparse` | `S3DISFusedDataset`, `ScannetDataset` | Often tied to sparse or PointGroup-style models. |
| Registration | `fragment3dmatch`, `patch3dmatch`, `fragmentkitti_sparse`, `test3dmatch`, `testeth`, `testtum`, `testkaist`, `testplanetary`, `modelnet_sparse_ss` | `General3DMatchDataset`, `KittiDataset`, test-set wrappers, `SiameseModelNetDataset` | Needs pair/fragment files, descriptors, ground-truth transforms, and often sparse backends. |

## ScanNet raw scene preflight

A ScanNet v2 raw scene directory normally contains per-scene files named with
the scene id:

```text
scans/
  scene0000_00/
    scene0000_00.aggregation.json
    scene0000_00.txt
    scene0000_00_vh_clean_2.0.010000.segs.json
    scene0000_00_vh_clean_2.ply
```

Run the bundled checker without downloads:

```bash
python sub-skills/datasets-transforms/scripts/check_scannet_layout.py --base-dir /path/to/scans
```

It reports missing files and exits non-zero when any scene is incomplete. It
does not contact the ScanNet servers or write files.

## ShapeNet quick-prototype notes

ShapeNet segmentation configs use normal vectors and category labels in several
variants. For quick training tests, prefer fixed/tiny fixtures when available or
short Hydra early-break runs. A real ShapeNet root may still require PyG
preprocessing and enough disk for processed data.

## S3DIS notes

S3DIS appears in two broad forms:

- 1x1/preprocessed S3DIS blocks from PyG.
- Fused/raw S3DIS areas split into chunks with Torch Points3D transforms.

Commands usually need a fold/test-area setting. Large fused preprocessing can be
expensive, so run transform/config checks before instantiating the full dataset.

## SemanticKITTI notes

SemanticKITTI configs are segmentation-focused and rely on the dataset's
sequence/file conventions. Validate root paths and class mappings before a full
run. Sparse variants require sparse backend checks when paired with sparse
models.

## Registration data notes

Registration configs are more file-protocol heavy than segmentation configs.
They can require pairs, fragment features, ground-truth logs, test split lists,
or overlap metadata. Use the [registration workflow reference](../../registration-workflows/references/registration-workflows.md) before launching registration evaluation.
