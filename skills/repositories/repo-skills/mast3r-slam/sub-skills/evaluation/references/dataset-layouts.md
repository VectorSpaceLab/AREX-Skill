# Dataset Layouts and Download Planning

## When to read

Read this when preparing benchmark data or checking why an evaluation command
cannot find inputs.

## Dataset roots used by the upstream scripts

| Suite | Default root | Required signs |
| --- | --- | --- |
| TUM RGB-D | `datasets/tum/` | Each sequence directory has `rgb.txt`, images, and `groundtruth.txt`. |
| 7-Scenes | `datasets/7-scenes/` | Each scene has `seq-01/*.color.png`; groundtruth files are bundled separately. |
| EuRoC | `datasets/euroc/` | Each sequence has `mav0/cam0/data.csv`, `mav0/cam0/data/`, and `mav0/cam0/sensor.yaml`. |
| ETH3D | `datasets/eth3d/train/` | Each sequence has `rgb.txt`, `calibration.txt`, and `groundtruth.txt`. |

## Sequence lists

TUM: `rgbd_dataset_freiburg1_360`, `rgbd_dataset_freiburg1_desk`,
`rgbd_dataset_freiburg1_desk2`, `rgbd_dataset_freiburg1_floor`,
`rgbd_dataset_freiburg1_plant`, `rgbd_dataset_freiburg1_room`,
`rgbd_dataset_freiburg1_rpy`, `rgbd_dataset_freiburg1_teddy`,
`rgbd_dataset_freiburg1_xyz`.

7-Scenes: `chess`, `fire`, `heads`, `office`, `pumpkin`, `redkitchen`, `stairs`.

EuRoC: `MH_01_easy`, `MH_02_easy`, `MH_03_medium`, `MH_04_difficult`,
`MH_05_difficult`, `V1_01_easy`, `V1_02_medium`, `V1_03_difficult`,
`V2_01_easy`, `V2_02_medium`, `V2_03_difficult`.

ETH3D has many train sequences; use `plan_evaluation.py --suite eth3d` for the
exact evaluation list and `plan_downloads.py --suite eth3d` for download URLs.

## Safe download planning

Use:

```bash
python sub-skills/evaluation/scripts/plan_downloads.py --suite euroc --commands
```

This prints `wget`/extract commands but does not run them. Ask before executing
because the archives are large and may require dataset-license awareness.
