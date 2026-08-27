---
name: data-preparation
description: "Prepare and validate KITTI or NuScenes data layouts, generated
  infos, reduced point clouds, ground-truth databases, dataset classes, and
  preprocessing configuration for the legacy SECOND data API."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data preparation

Use this sub-skill when the task is to validate a KITTI/NuScenes root, plan info
or ground-truth-database generation, select a dataset class, adapt a custom
lidar dataset, or tune voxel/preprocess/database-sampling fields. It provides
static and CPU-safe guidance only. It does **not** claim that detector
training, evaluation, or the legacy runtime has been executed successfully.

## Route first

- Read [data-formats.md](references/data-formats.md) for directory, info-pickle,
  point, annotation, box, and coordinate contracts.
- Read [workflows.md](references/workflows.md) for the ordered KITTI/NuScenes
  preparation plans, commands, generated artifact names, and custom-dataset
  route.
- Read [api-reference.md](references/api-reference.md) for source-authoritative
  signatures, registry names, protobuf fields, and preprocessing semantics.
- Read [troubleshooting.md](references/troubleshooting.md) before changing an
  install, path, config, or generated artifact.
- Run the bundled non-mutating checker before any command that writes data:

```bash
python <skill-root>/scripts/validate_dataset_layout.py --help
python <skill-root>/scripts/validate_dataset_layout.py kitti --root <KITTI_ROOT>
python <skill-root>/scripts/validate_dataset_layout.py nuscenes --root <NUSC_ROOT> --version v1.0-trainval --max-sweeps 10
```

The helper never downloads, creates, deletes, rewrites, or unpickles dataset
files. It exits nonzero and prints stable `ERROR:` lines for an invalid layout.
An empty `velodyne_reduced/` directory is valid; its files are expected only
after reduced-cloud preparation.

## Decision checklist

1. Identify the dataset (`kitti` or `nuscenes`), root, split/version, desired
   info file, dataset class, point-feature width, and whether velocity boxes
   are intended.
2. Validate the directory and file-stem relationships. Do not infer a full
   dataset from a directory existing alone; source generation reads actual
   images, calibration, lidar, labels, or NuScenes metadata.
3. Choose the class and config as a pair. KITTI uses `KittiDataset`; NuScenes
   uses `NuScenesDataset`, a `D2`–`D8` subsample class, or the matching `Velo`
   class. The config's `kitti_*` field names are historical and are used for
   both datasets.
4. Generate infos, then reduced KITTI clouds where applicable, then the ground
   truth database. Record the exact generated filenames and rerun generation
   after source/config changes that alter their schema.
5. Check coordinate conventions, box dimensionality, class spelling, and
   point feature width before enabling preprocessing or database sampling.
6. Keep training/evaluation routing in
   [training-and-inference](../training-and-inference/SKILL.md). Route box
   transforms, visualization, and evaluation-format questions to
   [geometry-and-evaluation](../geometry-and-evaluation/SKILL.md).

## Boundaries and historical limits

- The checkout has no setup metadata. Treat package installation/import as an
  environment concern, not as proof that data or detector execution works.
- The model/data path uses legacy spconv and Numba APIs. Modern spconv 2.x is
  not proven compatible; do not recommend an unguarded migration as a fix.
- The public project guidance is historical and marks this code as deprecated.
  Prefer a maintained detector for new production work, but preserve these
  contracts when a legacy artifact must be prepared.
- `create_data.py` performs writes and is described, not bundled here. Use the
  validator first and make a backup or use a disposable output root. Never
  claim detector execution was verified from preparation success.

## Expected handoff

Report: validator command and result; root/version/class; info and database
paths; point/box feature widths; coordinate assumptions; selected preprocess
and sampler fields; files generated or still missing; and any blocked optional
dependency or legacy-runtime limitation. A static pass is not a training or
evaluation pass.
