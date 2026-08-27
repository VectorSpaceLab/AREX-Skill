---
name: datasets-demonstrations
description: "Guides Researchers through RoboCasa dataset registries, dataset
  soups, local LeRobot and legacy HDF5 inspection, playback, conversion, and
  dataset-backed setup."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# RoboCasa datasets and demonstrations

Use this sub-skill for RoboCasa 1.0.1 dataset discovery, local readiness checks,
demonstration sampling, playback selection, and format conversion planning. Treat
registry metadata, downloaded data, simulation assets, and rendering support as
separate readiness layers.

## Route first

- Read [API reference](references/api-reference.md) for exact registry signatures,
  source tokens, path resolution, horizons, task sets, and soups.
- Read [data formats](references/data-formats.md) before accessing samples,
  selecting playback flags, or converting legacy HDF5.
- Read [workflows](references/workflows.md) for safe registry-to-local-data,
  inspection, playback, conversion, and dataset-backed environment sequences.
- Read [troubleshooting](references/troubleshooting.md) before retrying downloads,
  changing dataset roots, or diagnosing missing replay files.
- Run [inspect_dataset.py](scripts/inspect_dataset.py) for a read-only local tree
  check. Run [plan_dataset_download.py](scripts/plan_dataset_download.py) to resolve
  registry paths and print opt-in commands without networking or writes.

## Operating gates

1. Confirm RoboCasa imports with its compatible package set. Version 1.0.1 pins
   MuJoCo 3.3.1 and NumPy 2.2.5, requires public `robosuite>=1.5.2`, and was
   inspected with LeRobot 0.3.3, h5py 3.16.0, and Gymnasium 0.29.1. Inspection
   registered 374 kitchen environments, but registration is not dataset, asset,
   reset, or playback proof.
2. Query registry metadata. Do **not** infer that a returned `path` exists: the
   registry resolves an expected location without downloading anything.
3. Check the local path and identify LeRobot versus legacy HDF5 before choosing
   any flags. A metadata-only tree is not a usable dataset.
4. Approve network, destination, storage, and overwrite behavior before invoking
   the package downloader. Dataset acquisition is an explicit, potentially
   multi-GB action.
5. Separate training access from simulator replay. Parquet/video data may be
   usable while replay still lacks `extras/dataset_meta.json`, episode
   `model.xml.gz`, `states.npz`, or full kitchen assets.
6. Keep playback/conversion bounded to a small episode count first. Conversion
   reconstructs environments, renders images, writes large outputs, and can
   replace an existing sibling `lerobot/` directory.

## Boundaries

- Route Gym/robosuite construction, reset/step behavior, and renderer setup to
  the root skill's `simulation-environments` sub-skill.
- Route task, scene, fixture, object, and kitchen-asset taxonomy to
  `tasks-scenes-assets`.
- Route live keyboard/SpaceMouse collection and interactive demonstration capture
  to `teleoperation-and-collection`.
- MimicGen-labelled registry entries refer to provided synthetic datasets. The
  optional MimicGen package was absent during inspection; do not claim synthetic
  generation readiness from dataset metadata alone.
- Full datasets and kitchen assets were not locally available during construction.
  Registry and CLI surfaces were verified, but full playback, conversion, dataset
  tests, and dataset-backed reset remain data-dependent.
