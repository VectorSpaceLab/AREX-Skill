# Data Layouts

These layouts match the parsers in MonoGS and the bundled download helpers.

## TUM RGB-D
Dataset root example: `datasets/tum/rgbd_dataset_freiburg1_desk/`

Required files:
- `rgb.txt`
- `depth.txt`
- `groundtruth.txt` or `pose.txt`

The parser reads frame paths from `rgb.txt` and `depth.txt`, then matches them against the pose file. The referenced image and depth files must exist under the same sequence root.

Expected shape:
```text
datasets/tum/rgbd_dataset_freiburg1_desk/
  rgb.txt
  depth.txt
  groundtruth.txt   # or pose.txt
  rgb/
  depth/
```

## Replica
Dataset root example: `datasets/replica/office0/`

Required files:
- `results/frame*.jpg`
- `results/depth*.png`
- `traj.txt`

The parser expects the color and depth frame counts to match, and `traj.txt` to contain at least one pose line per frame.

Expected shape:
```text
datasets/replica/office0/
  results/
    frame000000.jpg
    depth000000.png
  traj.txt
```

## EuRoC
Dataset root example: `datasets/euroc/mh02/`

Required files:
- `mav0/cam0/data/*.png`
- `mav0/cam1/data/*.png`
- `mav0/state_groundtruth_estimate0/data.csv`

The stereo parser expects both camera streams to have the same frame count and uses `start_idx` to skip the first frames.

Expected shape:
```text
datasets/euroc/mh02/
  mav0/
    cam0/
      data/
        1403636579763555584.png
    cam1/
      data/
        1403636579763555584.png
    state_groundtruth_estimate0/
      data.csv
```

## RealSense
Live RealSense configs do not depend on a dataset tree. They require a camera, USB-3 connectivity, and the optional `pyrealsense2` package.

If `configs/live/realsense_rgbd.yaml` carries a `dataset_path`, treat it as a user-managed recording directory and check only that the directory exists.

## `--check-files` behavior
`scripts/validate_monogs_config.py --check-files` checks:
- the dataset root exists
- the manifest files or frame directories exist
- the frame references in TUM manifests resolve to real files
- the Replica color and depth frame counts match
- the EuRoC stereo directories and pose CSV exist
- a configured RealSense recording path exists when one is supplied
