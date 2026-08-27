# Data acquisition and download boundaries

This reference records prerequisites and destination layouts from the public
repository's download notes. It is intentionally not an automatic downloader:
validation and skill use must not start network operations, clone repositories,
install Git LFS, or accept dataset terms on a user's behalf.

## General boundary

Before obtaining data, the operator must independently confirm the dataset's
license, research/commercial-use terms, credentials, institutional approval,
network policy, disk quota, and the provenance of any mirror. Keep credentials
out of YAML, shell history, reports, and the skill tree. A successful clone is
not proof that a dataset may be redistributed.

The repository README says Git LFS must be installed and initialized for the
provided Replica and TUM sources. It points users to the official ScanNet and
ScanNet++ access procedures rather than supplying credentials. Follow those
official procedures manually and record only the resulting local destination
and version metadata.

## Replica reference layout

The reference script creates a `data` directory and clones the public
`Replica-SLAM` dataset mirror there. The expected scene paths used by the
configs are:

```text
data/Replica-SLAM/Replica/office0/
data/Replica-SLAM/Replica/office1/
...
data/Replica-SLAM/Replica/room1/
data/Replica-SLAM/Replica/room2/
```

The checked-in `room0.yaml` instead points at
`data/Replica-SLAM/room0/`; verify the actual mirror layout and correct that
path explicitly if needed. Do not silently create a second copy or change the
scene name. Each selected scene must ultimately contain `results/frame*.jpg`,
`results/depth*.png`, and `traj.txt` as described in
[data-formats.md](data-formats.md).

## TUM_RGBD reference layout

The reference script creates `data` and clones the public `TUM_RGBD-SLAM`
dataset mirror. Scene configs expect:

```text
data/TUM_RGBD-SLAM/rgbd_dataset_freiburg1_desk/
data/TUM_RGBD-SLAM/rgbd_dataset_freiburg2_xyz/
data/TUM_RGBD-SLAM/rgbd_dataset_freiburg3_long_office_household/
```

Each scene must expose `rgb.txt`, `depth.txt`, and a usable
`groundtruth.txt` or `pose.txt`. TUM calibration is sequence-specific; use the
matching scene config rather than borrowing Replica or ScanNet intrinsics.

## ScanNet and ScanNet++

The repository does not provide automatic scripts for these datasets. Obtain
ScanNet through its official access process and place each scene under the
configured `data/scannet/scans/<scene-id>` directory (or use an explicit
`--input_path`). The loader expects `color`, `depth`, and `pose` subdirectories.

Obtain ScanNet++ through its official access process and place each scene under
`data/scannetpp/data/<scene-id>` (or override the input path). The loader uses
the DSLR subset and requires `dslr/train_test_lists.json`,
`dslr/nerfstudio/transforms_undistorted.json`,
`dslr/undistorted_images/`, and `dslr/undistorted_depths/`. Access packages can
have optional modalities; do not report a scene as ready until the exact
selected split and camera metadata are present.

## Safe staging checklist

1. Choose one scene and destination; do not mix mirrors or scene IDs.
2. Read and accept terms through the dataset owner's process, outside this
   skill.
3. Confirm the destination has enough space and that credentials are available
   without embedding them in scripts.
4. Stage or mount data manually, then run `validate_config.py --require-data
   --path-base <working-root> <config>`.
5. If a path differs from the template, pass a final explicit `--input_path`
   and validate that override's equivalent YAML or fixture. Keep the mismatch
   documented for reproducibility.

Never turn a failed download, missing credential, or license uncertainty into
an instruction to bypass access controls. Never bundle or execute the original
network clone commands as part of a preflight.
