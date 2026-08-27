# Repo provenance

| Field | Value |
| --- | --- |
| repository | ScaledYOLOv4 |
| source_commit | `f5581d7bfec5d46c5bf8a18580153deafc378ae7` |
| branch | `yolov4-large` |
| exact_tag | none |
| working_tree_state | dirty |
| dirty_paths_summary | `skills/` local skill-generation artifacts were present during capture |
| package_version | not declared in packaging metadata |
| remote_url | https://github.com/WongKinYiu/ScaledYOLOv4.git |

## Evidence paths used

All evidence paths below are relative to the repository root.

- `README.md`
- `detect.py`
- `test.py`
- `train.py`
- `models/common.py`
- `models/experimental.py`
- `models/export.py`
- `models/yolo.py`
- `models/yolov4-csp.yaml`
- `models/yolov4-p5.yaml`
- `models/yolov4-p6.yaml`
- `models/yolov4-p7.yaml`
- `utils/datasets.py`
- `utils/general.py`
- `utils/google_utils.py`
- `utils/torch_utils.py`
- `data/coco.yaml`
- `data/hyp.finetune.yaml`
- `data/hyp.scratch.yaml`
- `skills/ScaledYOLOv4.log`

## Bundled runtime mirror

The generated skill includes a runtime mirror copied from the evidence paths above so future agents can run concrete entrypoints without the original checkout:

- `runtime/detect.py`
- `runtime/test.py`
- `runtime/train.py`
- `runtime/models/`
- `runtime/utils/`
- `runtime/data/`
- `runtime/demo/`

## Snapshot notes

- The repository is script-first rather than package-first.
- The model stack requires the CUDA Mish extension in `models/common.py`.
- CLI help and synthetic forward checks were used to confirm the public runtime surface before the skill tree was written.
- The repair pass packaged executable source, model modules, utility modules, and YAML/demo configs under `runtime/` to remove helper dependence on the original checkout.
