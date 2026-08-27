# Input Data Formats

## When to read

Read this before validating a `--dataset` value or diagnosing incorrect dataset
class selection.

## Dataset selection logic

`load_dataset(dataset_path)` splits the path on `/` and checks tokens in this
order:

1. `tum` -> TUM RGB-D directory.
2. `euroc` -> EuRoC MAV directory.
3. `eth3d` -> ETH3D SLAM directory.
4. `7-scenes` -> 7-Scenes directory.
5. `realsense` -> live RealSense device.
6. `webcam` -> OpenCV webcam device.
7. Video extension `mp4`, `avi`, `MOV`, `mov` -> video loader.
8. Otherwise -> folder of RGB `.png` files.

Because matching is token-based, path naming matters. If an arbitrary directory
contains a substring such as `tum`, MASt3R-SLAM will choose the corresponding
specialized loader.

## Expected layouts

| Input type | Required signs |
| --- | --- |
| TUM RGB-D | directory token `tum`; `rgb.txt`; images referenced by the second column of `rgb.txt`; `groundtruth.txt` for metrics. |
| EuRoC | token `euroc`; `mav0/cam0/data.csv`; images under `mav0/cam0/data/`; `mav0/cam0/sensor.yaml`. |
| ETH3D | token `eth3d`; `rgb.txt`; `calibration.txt`; sequence `groundtruth.txt` for metrics. |
| 7-Scenes | token `7-scenes`; images under `seq-01/*.color.png`; external groundtruth text is used for metrics. |
| RGB folder | directory with one or more `.png` images; timestamps are generated at 30 Hz. |
| MP4/AVI/MOV | file with matching extension; `torchcodec` speeds loading but OpenCV fallback is supported. |
| RealSense | `--dataset realsense`; requires camera hardware and `pyrealsense2`. |
| Webcam | `--dataset webcam`; requires OpenCV camera access. |

## Validation helper

Use:

```bash
python sub-skills/run-slam/scripts/validate_inputs.py --dataset <path-or-device> --strict
```

The helper does not load MASt3R or checkpoints; it only checks file layout and
calibration YAML structure.
