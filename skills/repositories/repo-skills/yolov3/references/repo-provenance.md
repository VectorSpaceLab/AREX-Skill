# Repo Provenance

Schema: `disco.repo-provenance.v1`

- Repository: `ultralytics/yolov3`
- Source remote: `https://github.com/ultralytics/yolov3.git`
- Branch: `master`
- Source commit: `97b87b1347d6d927d27227d2225140da38e4d308`
- Dirty state at construction: generated skill artifacts were untracked; source files were not modified for skill construction.
- Package identity: `YOLOv3` metadata in `pyproject.toml`; no stable installed distribution version was available from the source metadata.
- Operating scope: detection-only YOLOv3, YOLOv3-SPP, and YOLOv3-tiny training, validation, inference, export, architecture inspection, and repo maintenance.

## Evidence paths

- Documentation and policy: `README.md`, `CONTRIBUTING.md`, `AGENTS.md`, `.github/workflows/ci-testing.yml`
- Packaging and dependencies: `pyproject.toml`, `requirements.txt`
- Native workflow scripts: `train.py`, `val.py`, `detect.py`, `export.py`, `hubconf.py`, `benchmarks.py`
- Models and architecture: `models/yolo.py`, `models/common.py`, `models/experimental.py`, `models/yolov3.yaml`, `models/yolov3-spp.yaml`, `models/yolov3-tiny.yaml`
- Data/config evidence: `data/coco128.yaml`, `data/scripts/get_coco128.sh`, `data/scripts/get_coco.sh`, `data/scripts/download_weights.sh`, `data/hyps/`
- Utilities: `utils/general.py`, `utils/downloads.py`, `utils/dataloaders.py`, `utils/loss.py`, `utils/metrics.py`, `utils/torch_utils.py`, `utils/loggers/`

## Refresh guidance

Refresh this skill when the source commit changes, when CLI flags in `train.py`, `val.py`, `detect.py`, or `export.py` change, when `hubconf.py` model names or signatures change, when `DetectMultiBackend` suffix handling changes, when dependency floors change, or when repository policy in `AGENTS.md`/CI changes.
