# Data preparation for UniAD

This reference is self-contained runtime guidance for preparing UniAD data assets. Source evidence used to distill it included the repository's `docs/DATA_PREP.md`, `tools/uniad_create_data.sh`, `tools/create_data.py`, the nuScenes converter implementation, and public config fields that set `data_root`, `info_root`, and the motion-anchor path.

## What UniAD expects

UniAD uses nuScenes with camera, lidar, CAN bus, and map extensions. The default public configs use these paths:

| Asset | Default path | Used by |
|---|---|---|
| Raw nuScenes data root | `data/nuscenes/` | BEVFormer, stage-1 track/map, stage-2 E2E datasets |
| Temporal info PKLs | `data/infos/nuscenes_infos_temporal_train.pkl`, `data/infos/nuscenes_infos_temporal_val.pkl` | Dataset annotations for train/val and default test-on-val |
| Motion anchors | `data/others/motion_anchor_infos_mode6.pkl` | Stage-2/E2E motion head |
| CAN bus extension | `data/nuscenes/can_bus/` | Ego-motion/CAN bus fields used by temporal BEV and planning labels |
| Map extension | `data/nuscenes/maps/` | Map vectorization, lane/map labels, planning and map evaluation |

The expected working layout is:

```text
UniAD/
├── projects/
├── tools/
├── ckpts/
└── data/
    ├── nuscenes/
    │   ├── can_bus/
    │   ├── maps/
    │   ├── lidarseg/              # official full-layout item; usually not the first UniAD failure
    │   ├── samples/
    │   ├── sweeps/
    │   ├── v1.0-trainval/
    │   ├── v1.0-test/             # needed for actual test-set conversion/submission workflows
    │   └── v1.0-mini/             # only for mini experiments, not a substitute for full metrics
    ├── infos/
    │   ├── nuscenes_infos_temporal_train.pkl
    │   └── nuscenes_infos_temporal_val.pkl
    └── others/
        └── motion_anchor_infos_mode6.pkl
```

For many validation/evaluation workflows the full trainval metadata plus `train`/`val` temporal info PKLs are sufficient. Actual test-set submission workflows additionally need the `v1.0-test` metadata and a test info PKL.

## Off-the-shelf assets

The maintainers published prepared UniAD data helper files in the `OpenDriveLab/UniAD2.0_R101_nuScenes` Hugging Face repository. These files are the safest starting point when the user already has the raw nuScenes data layout:

```bash
mkdir -p data/infos data/others
wget -O data/infos/nuscenes_infos_temporal_train.pkl \
  https://huggingface.co/OpenDriveLab/UniAD2.0_R101_nuScenes/resolve/main/data/nuscenes_infos_temporal_train.pkl
wget -O data/infos/nuscenes_infos_temporal_val.pkl \
  https://huggingface.co/OpenDriveLab/UniAD2.0_R101_nuScenes/resolve/main/data/nuscenes_infos_temporal_val.pkl
wget -O data/others/motion_anchor_infos_mode6.pkl \
  https://huggingface.co/OpenDriveLab/UniAD2.0_R101_nuScenes/resolve/main/data/motion_anchor_infos_mode6.pkl
```

Raw nuScenes data, CAN bus, and map extensions are not bundled by this skill. They must be downloaded from the official nuScenes distribution according to the nuScenes license and placed or symlinked into `data/nuscenes/`.

## Generating temporal info PKLs

UniAD's data conversion workflow is equivalent to:

```bash
PYTHONPATH="<UniAD repo root>:${PYTHONPATH:-}" \
python <UniAD repo root>/tools/create_data.py nuscenes \
  --root-path <UniAD repo root>/data/nuscenes \
  --out-dir <UniAD repo root>/data/infos \
  --extra-tag nuscenes \
  --version v1.0 \
  --canbus <UniAD repo root>/data/nuscenes
```

Use the bundled dry command builder instead of reconstructing this by hand:

```bash
python skills/disco/uniad/sub-skills/data-preparation/scripts/build_data_command.py \
  --uniad-root <UniAD repo root> --version v1.0
```

Command semantics distilled from `tools/create_data.py`:

- positional dataset is `nuscenes`;
- `--root-path` points to the raw nuScenes root, normally `data/nuscenes`;
- `--canbus` points to the root that contains `can_bus`, normally the same `data/nuscenes`;
- `--out-dir` is where the temporal PKLs are written, normally `data/infos`;
- `--extra-tag nuscenes` produces `nuscenes_infos_temporal_*.pkl`;
- `--max-sweeps` defaults to `10`;
- `--version v1.0` makes the converter process `v1.0-trainval` and `v1.0-test` internally;
- `--version v1.0-mini` processes only the mini split.

The converter also exports camera 2D annotation JSON files next to the PKLs using names ending in `_mono3d.coco.json`.

## Validate before training/evaluation

Run the bundled validator from any checkout or copied skill location:

```bash
python skills/disco/uniad/sub-skills/data-preparation/scripts/check_uniad_data_layout.py \
  --uniad-root <UniAD repo root> --version v1.0 --stage e2e
```

For a mini-only sanity setup:

```bash
python skills/disco/uniad/sub-skills/data-preparation/scripts/check_uniad_data_layout.py \
  --uniad-root <UniAD repo root> --version v1.0-mini --stage stage1
```

A clean E2E readiness check should find:

- `data/nuscenes/samples/` and `data/nuscenes/sweeps/`;
- the requested nuScenes version directory (`v1.0-trainval`, `v1.0-test`, or `v1.0-mini`);
- `data/nuscenes/can_bus/`;
- `data/nuscenes/maps/` and its expansion map files;
- `data/infos/nuscenes_infos_temporal_train.pkl` and `data/infos/nuscenes_infos_temporal_val.pkl` for train/val workflows;
- `data/others/motion_anchor_infos_mode6.pkl` for stage-2/E2E.

## Config path caution for generated PKLs

The public configs set:

```python
data_root = "data/nuscenes/"
info_root = "data/infos/"
ann_file_train = info_root + "nuscenes_infos_temporal_train.pkl"
ann_file_val = info_root + "nuscenes_infos_temporal_val.pkl"
ann_file_test = info_root + "nuscenes_infos_temporal_val.pkl"
```

The data converter may write `lidar_path`, camera `data_path`, and sweep paths that already include `data/nuscenes/` or an absolute dataset root. If those paths are embedded in the PKL and the config also prepends `data_root = "data/nuscenes/"`, data loading can look for duplicated paths such as `data/nuscenes/data/nuscenes/samples/...`.

Safe choices:

1. Prefer the off-the-shelf PKLs if they match the expected config path convention.
2. If using generated PKLs that include root-prefixed paths, set `data_root = ""` in the active config or otherwise ensure the dataset loader receives paths exactly as stored in the PKL.
3. Keep `info_root` pointing to the directory that contains the temporal PKLs.
4. Re-run the bundled validator with PKL scanning enabled to surface path-root risk warnings.

Do not change model architecture or launch commands in this sub-skill; hand those tasks to the appropriate sibling sub-skill after data readiness is established.
