---
name: datasets-and-preprocessing
description: "Route Det3D dataset layout, metadata conversion, annotation,
  loading, voxelization, and pipeline-preprocessing tasks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Datasets and Preprocessing

Use this route for KITTI, nuScenes, or Lyft directory layouts; info/database
creation; annotation schemas; point-cloud loading; voxel/pillar preprocessing;
transforms; and dataset validation. Read [data-formats.md](references/data-formats.md)
before changing a config and [data-preparation.md](references/data-preparation.md)
before running a conversion.

## Workflow

1. Identify dataset/version/split and make the root explicit.
2. Run `scripts/validate_dataset_layout.py` as a non-mutating preflight.
3. Confirm generated info paths, DB-info paths, sweep count, class names, and
   coordinate conventions match the config.
4. Read [pipeline-api.md](references/pipeline-api.md) for transform ordering,
   fields, and tensor/voxel contracts.
5. Only then plan `create_data` or training/evaluation; conversion can write
   many files and may require dataset SDKs and a GPU environment.

Dataset conversion, ground-truth database creation, and full loaders are not
validated by an empty directory or a config parse. Keep data and output paths
user-supplied; never embed checkout-specific paths in reusable instructions.

For model/config coupling use `configuration-and-models`; for CLI execution use
`training-and-evaluation`; for missing SDKs or compiled ops use `runtime-ops`.
