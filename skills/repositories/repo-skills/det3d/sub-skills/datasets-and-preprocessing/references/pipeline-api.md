# Pipeline and Voxel Contracts

Dataset pipelines are composed transforms. The loader creates a sample dict;
loading, preprocessing, augmentation, formatting, and collection must preserve
the fields expected by the detector. Common contracts include point arrays,
images/calibration (when used), ground-truth boxes/names, sweep metadata,
voxel coordinates, voxel counts, and per-sample metadata.

Order matters. Load the raw point/annotation data before geometric transforms;
apply the same coordinate transform to points, boxes, and calibration-derived
values; filter classes and ranges before target assignment; then format and
collate the batch. A transform that only updates points but not boxes creates
silent label drift.

Voxel/pillar parameters must agree across config and preprocessing: point-cloud
range, voxel size, max points per voxel, max voxels, feature dimensions, and
whether the model expects xyz/intensity/time or augmented features. For
multi-sweep nuScenes, verify sweep timestamps and velocity fields.

Use small synthetic arrays only for isolated pure transform tests. They cannot
prove dataset SDK behavior, calibration correctness, or detector performance.
