# Data-preparation workflows

This reference is a bounded, filesystem-first playbook. Commands use ordinary
shell paths and should be adapted to the user's environment. They do not
imply that the legacy MapTR stack or custom CUDA operators are installed.

## 1. Establish a safe working contract

Before touching data, record:

- dataset and release (`nuScenes v1.0` or `Argoverse2 Sensor`),
- raw root, CAN-bus root if applicable, and output root,
- whether the requested result is train, val, or test,
- expected `ann_file` and `map_ann_file`,
- maximum converter workers and available disk space,
- whether the source data may be read or modified.

Use absolute paths and do not use a data root that is also a skill or source
code root. The bundled checker only reads metadata and directory entries:

```bash
python <skill-root>/scripts/check_dataset_layout.py --help
python <skill-root>/scripts/check_dataset_layout.py \
  --dataset nuscenes --root /data/maptr/nuscenes \
  --canbus-root /data/maptr --json
```

The first command should print dataset choices, required options, exit-status
behavior, and `--self-test`. The second should print a JSON object containing
`dataset`, `checks`, `errors`, and `warnings`; a clean raw root has no errors
but may have annotation warnings unless `--check-annotations` is supplied.

## 2. Dependency probe, before conversion

The project documents this legacy target:

```bash
python --version                 # expected Python 3.8.x
python -c "import torch; print(torch.__version__, torch.version.cuda)"
python -c "import mmcv; print(mmcv.__version__)"
python -c "import mmdet; print(mmdet.__version__)"
python -c "import mmseg; print(mmseg.__version__)"
python -c "import shapely; print(shapely.__version__)"
python -c "import av2; print('av2 import ok')"       # AV2 only
```

The documented package targets are PyTorch 1.9.1+cu111, mmcv-full 1.4.0,
mmdet 2.14.0, mmsegmentation 0.14.1, and shapely 1.8.5.post1, with Python 3.8
and `av2`. Import probes are informative only: binary compatibility, the
mmdetection3d component, and Geometric Kernel Attention still need their own
checks. Stop before conversion if an import fails, if the Python major/minor
version is incompatible with the planned wheels, or if the AV2 API is absent
for an AV2 conversion.

Do not run a package installer as part of the layout checker. Do not infer a
successful custom extension build from `torch.cuda.is_available()` alone.

## 3. nuScenes preparation

Expected raw layout (some release metadata may contain additional files):

```text
<data-parent>/
  can_bus/
  nuscenes/
    maps/
    samples/
    sweeps/
    v1.0-trainval/
    v1.0-test/
```

`--canbus` is passed to `NuScenesCanBus(dataroot=...)`; therefore the required
CAN expansion directory is `<canbus-root>/can_bus`. When using the documented
command, `<canbus-root>` is the parent of the nuScenes root. A `can_bus`
directory nested under `nuscenes/` is not accepted as the canonical location
by this route. The converter can return zero CAN values for server scenes,
but a missing expansion root is still a preparation failure because it hides a
layout mistake.

Run the full-release converter only after the checker passes:

```bash
python tools/create_data.py nuscenes \
  --root-path /data/maptr/nuscenes --out-dir /data/maptr/nuscenes \
  --extra-tag nuscenes --version v1.0 --canbus /data/maptr \
  --max-sweeps 10
```

The dispatch contract in `tools/create_data.py` is useful when adapting a
plan: `kitti` invokes Kitti info/reduced-cloud/2D export and a ground-truth
database; `nuscenes` invokes the modified temporal nuScenes converter and 2D
export; `lyft` invokes train/test info creation; `waymo` converts split data to
Kitti format before info generation; `scannet`, `s3dis`, and `sunrgbd` invoke
indoor info generation. These other branches do not produce MapTR's
nuScenes/AV2 vector-map pkl files and are out of scope here. `create_data.py`
has no AV2 branch; use the dedicated AV2 converter.

For full `v1.0`, the expected outputs are:

```text
<data-root>/nuscenes_infos_temporal_train.pkl
<data-root>/nuscenes_infos_temporal_val.pkl
<data-root>/nuscenes_infos_temporal_test.pkl
```

The trainval files contain a dictionary with an `infos` list and `metadata`;
each info records lidar path, camera paths/calibration, sweeps, temporal
`prev`/`next` links, scene, pose, CAN bus, timestamp, and `map_location`. The
MapTR custom dataset uses `ann_file` to load these infos. Map geometry is read
from `maps/` by `VectorizedLocalMap`, not embedded in the temporal pkl.

## 4. Argoverse2 preparation

Expected top-level layout:

```text
<data-root>/
  train/<log-id>/
    sensors/...                     # loader-managed sensor tree
    map/log_map_archive_<name>.json
  val/<log-id>/
    sensors/...
    map/log_map_archive_<name>.json
  test/<log-id>/
    sensors/...
    map/log_map_archive_<name>.json
```

The exact sensor subdirectories are owned by the AV2 Sensor API, but the
converter queries lidar timestamps and these seven camera names:
`ring_front_center`, `ring_front_right`, `ring_front_left`,
`ring_rear_right`, `ring_rear_left`, `ring_side_right`, and `ring_side_left`.
A log with no usable synchronized camera/lidar sample may produce no samples;
the converter reports discarded samples. Every log must have exactly one
`log_map_archive_*.json` in its `map/` directory. The checker validates that it
is nonempty valid JSON; the AV2 API remains responsible for semantic map
schema validation.

Run with a bounded worker count:

```bash
python <skill-root>/scripts/check_dataset_layout.py \
  --dataset av2 --root /data/maptr/argoverse2/sensor
python tools/data_converter/av2_converter.py \
  --data-root /data/maptr/argoverse2/sensor --nproc 8
```

The converter loops over `train`, `val`, and `test` regardless of whether a
caller needs all three, removes six known failing log ids, uses a multiprocessing
pool, and writes:

```text
<data-root>/av2_map_infos_train.pkl
<data-root>/av2_map_infos_val.pkl
<data-root>/av2_map_infos_test.pkl
```

Each output is a dictionary with `samples` and `id2map`. A sample has
`e2g_translation`, `e2g_rotation`, `cams`, `lidar_fpath`, string `timestamp`,
`log_id`, and `token`. Each `cams` entry has an image path, camera intrinsics,
and camera extrinsics. `id2map[log_id]` has `divider`, `ped_crossing`, and
`boundary` lists. `CustomAV2LocalMapDataset.load_annotations` sorts `samples`
by timestamp and stores `id2map`; the vectorizer uses `log_id` to select map
elements and transforms city-frame geometry into the ego frame.

## 5. Post-conversion and handoff

Re-run the checker with `--check-annotations`. For nuScenes, check the train
and val temporal pkl expected by the selected config. For AV2, check train and
val pkl at the sensor root; checking test too is useful because the converter
always attempts it. Then inspect a small number of records with a separate
read-only pkl inspection utility if the required Python dependencies are
available. Do not load private data in a generic validation script.

A complete handoff states whether the result is only a layout pass or a real
conversion, lists exact output files and counts, and records skipped or
malformed logs. Route `pc_range`, `fixed_ptsnum_per_line`, and class names to
[model-configuration](../../model-configuration/SKILL.md); route commands to
[training-evaluation](../../training-evaluation/SKILL.md).