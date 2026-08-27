# Data Preparation

The documented entry point is `tools/create_data.py`, exposed through Fire:

```text
kitti_data_prep --root_path DATASET_ROOT
nuscenes_data_prep --root_path DATASET_ROOT --version v1.0-trainval --nsweeps 10
lyft_data_prep --root_path DATASET_ROOT
```

Treat these as plans, not safe default commands. They inspect source datasets,
create metadata/info files, and may create a ground-truth database. Preflight:

- verify the SDK (`nuscenes-devkit` or Lyft SDK) and version;
- confirm source root, split/version, output paths, and free disk space;
- choose a writable output directory and preserve the source dataset;
- ensure class names and split files match the target config;
- for nuScenes, keep `--nsweeps` synchronized with `n_sweeps` and annotation
  filenames;
- run on the documented GPU-capable environment when the conversion path uses
  GPU-dependent preprocessing.

Never run conversion against an unknown root or an empty fixture as proof of
correctness. If a conversion fails, retain the first missing-file/SDK error and
validate paths before changing package versions.
