# Dataset Formats

## KITTI

The documented KITTI root contains `training/` and `testing/`. Training holds
`image_2/` (optional for point-only work), `calib/`, `label_2/`, `velodyne/`,
and a `velodyne_reduced/` directory. Testing omits labels. Split files under
the package identify train/val membership. Keep calibration, point-cloud,
image, and label frame ids aligned; an apparently valid directory with mixed
ids is not a valid dataset.

## nuScenes

The trainval/test roots contain `samples/`, `sweeps/`, `maps/`, and a versioned
metadata directory such as `v1.0-trainval` or `v1.0-test`. `n_sweeps` changes
both preprocessing cost and the expected info files. The config's annotation
paths must name the same sweep count used during preparation.

## Lyft

The documented layout separates `trainval/` and `test/`, each with `data/`,
`lidar/`, and `maps/`. The SDK and split/version assumptions must match the
configuration.

For every dataset, validate class names, split files, annotation/info paths,
point feature dimensions, coordinate frame, and whether velocity/sweeps are
present before blaming the detector.
