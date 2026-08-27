# Runtime bundle

The generated ScaledYOLOv4 skill now includes a self-contained `runtime/` mirror of the concrete executable source and configs used by the main workflows.

## Bundled executable mirror

- `runtime/README.md`
- `runtime/detect.py`
- `runtime/test.py`
- `runtime/train.py`
- `runtime/models/export.py`
- `runtime/models/yolo.py`
- `runtime/models/common.py`
- `runtime/models/experimental.py`
- `runtime/utils/datasets.py`
- `runtime/utils/general.py`
- `runtime/utils/google_utils.py`
- `runtime/utils/torch_utils.py`
- `runtime/data/coco.yaml`
- `runtime/data/demo.yaml`
- `runtime/data/hyp.scratch.yaml`
- `runtime/data/hyp.finetune.yaml`
- `runtime/demo/images/train/img1.png`
- `runtime/demo/images/val/img2.png`
- `runtime/demo/labels/train/img1.txt`
- `runtime/demo/labels/val/img2.txt`
- `runtime/models/yolov4-csp.yaml`
- `runtime/models/yolov4-p5.yaml`
- `runtime/models/yolov4-p6.yaml`
- `runtime/models/yolov4-p7.yaml`

## Why it exists

The root and sub-skill helper scripts default to this mirror so they do not depend on the original repository checkout for their concrete entrypoints, model modules, or YAML/config files.

## What still comes from the user

- Real weights checkpoints for training, evaluation, detection, or export.
- Real image or video sources for inference.
- Real datasets when the user is going beyond the bundled validation fixtures.

## How to use it

Treat `runtime/` as the bundled checkout that future agents can run directly when they need the repo's actual source entrypoints. The higher-level skill references explain which helper script to use first for each workflow.

For concrete execution, prefer the bundled wrappers instead of manually changing directories:

- `scripts/run_runtime_entrypoint.py detect -- ...`
- `scripts/run_runtime_entrypoint.py test -- ...`
- `scripts/run_runtime_entrypoint.py train -- ...`
- `scripts/run_runtime_entrypoint.py export -- ...`
- `sub-skills/inference/scripts/run_detection.py -- ...`
- `sub-skills/evaluation/scripts/run_evaluation.py -- ...`
- `sub-skills/training/scripts/run_training.py -- ...`
- `sub-skills/export/scripts/run_export.py -- ...`

Use `--dry-run` with these wrappers before long training, validation, detection, or conversion jobs. Use `scripts/check_runtime_bundle.py` to verify that the concrete source and config files are present.
