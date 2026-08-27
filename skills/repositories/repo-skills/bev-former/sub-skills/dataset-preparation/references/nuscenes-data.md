# nuScenes layout and CAN-bus prep

This sub-skill validates the tree that the BEVFormer dataset-preparation flow produces. It does not replace the upstream converter; it checks that the resulting layout is ready for camera-only BEVFormer and BEVFormerV2 configs.

## Raw nuScenes tree

A full nuScenes release should expose the raw data under a single `data-root` directory, for example:

```text
data-root/
├── maps/
├── samples/
│   ├── CAM_BACK/
│   ├── CAM_BACK_LEFT/
│   ├── CAM_BACK_RIGHT/
│   ├── CAM_FRONT/
│   ├── CAM_FRONT_LEFT/
│   ├── CAM_FRONT_RIGHT/
│   └── LIDAR_TOP/
├── sweeps/
│   ├── CAM_BACK/
│   ├── CAM_BACK_LEFT/
│   ├── CAM_BACK_RIGHT/
│   ├── CAM_FRONT/
│   ├── CAM_FRONT_LEFT/
│   ├── CAM_FRONT_RIGHT/
│   └── LIDAR_TOP/
├── v1.0-trainval/
├── v1.0-test/
├── nuscenes_infos_temporal_train.pkl
├── nuscenes_infos_temporal_val.pkl
└── nuscenes_infos_temporal_test.pkl
```

Notes:

- The BEVFormer camera-only configs still depend on the raw LiDAR folders because the temporal info builder reads the LiDAR top sample, sweep chain, and pose metadata.
- `maps/` and the `v1.0-*` version folders must sit directly under the nuScenes root.
- If you only need the full training split, the checker still requires the train and val temporal files.

## CAN-bus expansion

- The CAN-bus archive is usually unpacked separately, commonly beside the nuScenes root as `can_bus/`.
- The dataset-preparation flow consumes the `pose` messages from the CAN-bus data.
- The converter builds an expanded numeric CAN-bus record per sample, and the dataset later rewrites the translation, rotation, and yaw slots when it assembles temporal queues.
- If CAN-bus data is missing for a scene, the upstream converter can fall back to zeroed values for that scene. That keeps conversion moving, but it is usually a sign that the CAN-bus tree is incomplete.

## Generated temporal files

The expected outputs are:

- `nuscenes_infos_temporal_train.pkl`
- `nuscenes_infos_temporal_val.pkl`
- `nuscenes_infos_temporal_test.pkl`

Keep the `data_root` in your config pointed at the directory that contains these files, and keep `ann_file` pointed at the matching temporal pkl for the split you are using.

For BEVFormer and BEVFormerV2, the generated temporal files are part of the dataset contract, not a model tweak. If you change the root or regenerate the files, update the config pair together.

## Generation recipe

The source project generated the temporal pkls by running its nuScenes converter with this argument contract:

```bash
python tools/create_data.py nuscenes \
  --root-path ./data/nuscenes \
  --out-dir ./data/nuscenes \
  --extra-tag nuscenes \
  --version v1.0 \
  --canbus ./data
```

Interpretation:

- `--root-path` is the raw nuScenes root that contains `samples/`, `sweeps/`, `maps/`, and version folders.
- `--out-dir` is where the temporal pkl files are written; BEVFormer configs normally expect it to be the same directory as `data_root`.
- `--extra-tag nuscenes` creates `nuscenes_infos_temporal_*.pkl`.
- `--version v1.0` expands into trainval and test conversion passes.
- `--canbus` points at the directory that contains the extracted `can_bus/` folder.

Use this as a parameter recipe. If the converter code is not available in the active working environment, do not fabricate temporal pkls; obtain a BEVFormer-compatible conversion environment or an already generated data root, then validate it with the bundled checker.

## Layout checker

Use the bundled checker to validate the tree before handing it to a training or evaluation workflow:

- [scripts/check_bevformer_nuscenes_layout.py](../scripts/check_bevformer_nuscenes_layout.py)

The checker is intentionally conservative: it verifies path presence and returns a non-zero exit code when the layout is incomplete.
