---
name: data-preparation
description: "This skill prepares and preflights MapTR nuScenes and Argoverse2
  data layouts, annotation contracts, and vector-map schemas before model
  execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MapTR data preparation

Use this route before training, evaluation, or visualization. It turns a raw
nuScenes or Argoverse2 download into a checked layout plan and tells the next
agent which generated files and vector schema MapTR expects. It does **not**
download data, run a full converter, install packages, or modify a user data
root.

## Fast path

1. Choose the dataset and make an explicit absolute data root.
2. Run the bundled [CPU-only layout checker](scripts/check_dataset_layout.py).
   It checks directories and file names; it does not import MapTR, `mmcv`,
   `nuscenes`, `av2`, or `torch`.

   ```bash
   python <skill-root>/scripts/check_dataset_layout.py \
     --dataset nuscenes --root /data/maptr/nuscenes --canbus-root /data/maptr \
     --check-annotations
   python <skill-root>/scripts/check_dataset_layout.py \
     --dataset av2 --root /data/maptr/argoverse2/sensor \
     --check-annotations
   ```

3. Resolve every `ERROR` before starting a converter. Use `--json` when a
   machine-readable report is needed. `--self-test` exercises valid and
   deliberately broken tiny fixtures without accessing external data.
4. Select a converter only after the raw layout passes. Record the exact
   command, version, output root, and worker count; preserve converter logs.
5. Re-run with `--check-annotations` after conversion. A passing layout check
   is not proof that images, calibration, transforms, or map geometry are
   numerically correct.

The checker returns exit code 0 only when all requested checks pass. It returns
1 for a missing required path, wrong placement, malformed map archive, or
missing requested annotation file. It never creates a directory in the data
root.

## Installation and safety gates

The documented dependency target is Python 3.8, PyTorch 1.9.1+cu111,
`mmcv-full==1.4.0`, `mmdet==2.14.0`, `mmsegmentation==0.14.1`, `timm`,
`mmdetection3d==0.17.2`, `shapely==1.8.5.post1`, and the `av2` API for AV2.
The project also documents installing its mmdetection3d component and the
Geometric Kernel Attention extension. Treat these versions as a compatibility
plan, not as a verified installation on the current machine. A legacy CUDA
compiler, matching `mmcv-full`, and a successful custom extension build are
not assumed here.

Install prerequisites in an isolated environment and prove imports before
conversion. Do not start with a large converter just to discover an import or
ABI mismatch. See the [workflow reference](references/workflows.md) for the
ordered probes and documented commands. Route model and extension choices to
[model-configuration](../model-configuration/SKILL.md), and route execution to
[training-evaluation](../training-evaluation/SKILL.md).

## Dataset choices and converter contracts

### nuScenes

The documented raw root is `data/nuscenes/`, with `maps/`, `samples/`,
`sweeps/`, and version metadata such as `v1.0-trainval/` and `v1.0-test/`.
The CAN bus expansion belongs beside the dataset root: with
`--root-path /data/maptr/nuscenes --canbus /data/maptr`, the converter looks
for `/data/maptr/can_bus/`, **not** `/data/maptr/nuscenes/can_bus/`.

Reference command for the full release:

```bash
python tools/create_data.py nuscenes \
  --root-path /data/maptr/nuscenes --out-dir /data/maptr/nuscenes \
  --extra-tag nuscenes --version v1.0 --canbus /data/maptr \
  --max-sweeps 10
```

`tools/create_data.py` dispatches `nuscenes` twice for a non-mini version: it
passes `v1.0-trainval`, then `v1.0-test`, to the nuScenes converter. The
trainval call writes `nuscenes_infos_temporal_train.pkl` and
`nuscenes_infos_temporal_val.pkl`; the test call writes
`nuscenes_infos_temporal_test.pkl`. A `v1.0-mini` request is handled once and
uses the mini split. The converter also performs 2D annotation export. MapTR's
map dataset consumes the temporal `infos` records and derives local vectors
from the map expansion at runtime.

### Argoverse2 Sensor

The documented root is `data/argoverse2/sensor/` with exactly the split level
`train/`, `val/`, and `test/`. Each log directory needs the sensor data used by
the loader and one map archive matching `map/log_map_archive_*.json`. The
converter is:

```bash
python tools/data_converter/av2_converter.py \
  --data-root /data/maptr/argoverse2/sensor --nproc 8
```

The CLI defaults to 64 workers; choose a bounded value for a first run. Its
`__main__` path processes `train`, `val`, and `test`, removes a fixed list of
known failing logs, queries lidar timestamps, chooses the closest image for
seven ring cameras, and discards samples with unsynchronized lidar/camera
paths. It loads one JSON map archive per log and writes, at the **sensor root**,
`av2_map_infos_train.pkl`, `av2_map_infos_val.pkl`, and
`av2_map_infos_test.pkl`. The config normally consumes train and val files and
uses `load_interval=4` for validation.

Full converters are reference-only for this route: they require downloaded
private data, third-party APIs, map parsing, multiprocessing, and writes to
large output files. The checker is the safe preflight; do not replace it with
a full conversion run on synthetic folders.

## MapTR data contract

For nuScenes configs, set `data_root` to the nuScenes directory,
`ann_file` to the matching temporal train/val pkl, and leave `map_ann_file`
for the map evaluation-format JSON (for example,
`nuscenes_map_anns_val.json`). `map_ann_file` is not a substitute for the
raw map expansion or the temporal annotation pkl. For AV2, set `data_root` to
the sensor directory and use `av2_map_infos_{train,val}.pkl`; the dataset
loader expects each pkl to contain `samples` and `id2map`, sorted by sample
timestamp. `map_ann_file` similarly names the map-format output used by
validation/test formatting.

Both custom datasets expose three map classes in the standard MapTR configs:
`divider` (label 0), `ped_crossing` (label 1), and `boundary` (label 2).
`VectorizedLocalMap` obtains nuScenes divider lines, pedestrian-crossing
polygons, and road/lane contour boundaries from the four supported map
locations. `VectorizedAV2LocalMap` obtains divider polylines, pedestrian
polygons, and drivable-area boundary polygons from the converter's `id2map`.
Unexpected vector class names are errors; do not silently remap them.

The configured fixed-point representation is 20 points per ground-truth and
predicted line. A nonempty `LiDARInstanceLines.fixed_num_sampled_points` has
shape `[N, 20, 2]`, in local x/y coordinates, clamped to the patch. Shifted
representations may have shape `[N, shifts, 20, 2]`; closed polygons receive
cyclic shifts, open lines receive forward/reverse variants, and padding uses
`-10000`. Empty vector sets must remain representable; never fabricate a
placeholder line. The patch is derived from `pc_range`: height is
`y_max-y_min`, width is `x_max-x_min`. For the common nuScenes range
`[-15,-30,-2,15,30,2]`, the local patch is `(60,30)` and x/y limits are
approximately `[-15,15]`/`[-30,30]`. AV2's common range reverses those planar
extents.

## Handoff and routing

Report: dataset and release, absolute roots, raw checks, converter command
planned or run, generated pkl names, map-archive count, map classes, fixed
point count, and any unresolved dependency or data-quality issue. Do not claim
native conversion or model execution from a filesystem-only pass.

For configuration values and `pc_range` consistency use
[model-configuration](../model-configuration/SKILL.md). For train/test and
runtime commands use [training-evaluation](../training-evaluation/SKILL.md).
For map annotation rendering and benchmark plots use
[visualization-benchmarking](../visualization-benchmarking/SKILL.md).
Use [workflows](references/workflows.md), [data formats](references/data-formats.md),
and [troubleshooting](references/troubleshooting.md) for detailed recovery.
