# CLI reference

## Bundled helper scripts

Use these first when you want a safe preflight check instead of starting a long run:

| Helper | Purpose | Notes |
| --- | --- | --- |
| `scripts/check_runtime_bundle.py` | Verify that the packaged `runtime/` mirror contains required source/config files | Safe, no dataset or checkpoint needed |
| `scripts/check_cli.py` | Check the parser/help surfaces for the public workflows against the bundled runtime mirror | Safe, no dataset or checkpoint needed |
| `scripts/check_model_forward.py` | Build a YAML model from the bundled runtime mirror and run a tiny synthetic forward pass | Needs the model stack and a CUDA-capable Mish extension for full validation |
| `scripts/run_runtime_entrypoint.py` | Execute bundled runtime entrypoints with correct cwd and `PYTHONPATH` | Use `--dry-run` before long jobs |
| `sub-skills/data-preparation/scripts/inspect_dataset.py` | Inspect dataset YAMLs, image lists, and label samples | Safe preflight for custom data |
| `sub-skills/training/scripts/prepare_training_run.py` | Validate a training plan and print the canonical command | Avoids accidental long training starts |
| `sub-skills/training/scripts/run_training.py` | Run bundled `runtime/train.py` | Concrete training entrypoint; use `--dry-run` first |
| `sub-skills/evaluation/scripts/prepare_evaluation_run.py` | Validate a validation/test plan | Helps catch missing weights or bad split paths early |
| `sub-skills/evaluation/scripts/run_evaluation.py` | Run bundled `runtime/test.py` | Concrete evaluation entrypoint; use `--dry-run` first |
| `sub-skills/inference/scripts/prepare_inference_run.py` | Validate a detection source and output plan | Good for file/folder/webcam/stream routing |
| `sub-skills/inference/scripts/run_detection.py` | Run bundled `runtime/detect.py` | Concrete detection entrypoint; use `--dry-run` first |
| `sub-skills/export/scripts/check_export_env.py` | Check optional export backends | Reports ONNX/CoreML availability |
| `sub-skills/export/scripts/run_export.py` | Run bundled `runtime/models/export.py` | Concrete export entrypoint; use `--dry-run` first |

## Bundled runtime mirror

The concrete workflow entrypoints live under `runtime/` and are copied from the source checkout so future agents do not need the original repository tree to run them:

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
- `runtime/data/hyp.scratch.yaml`
- `runtime/data/hyp.finetune.yaml`

## Main workflow option groups

### Training planning

Key choices:

- weights vs. scratch training
- dataset YAML and hyperparameter YAML
- image sizes for train/test
- batch size, device, and distributed launch choices
- resume, `single_cls`, `multi_scale`, `sync_bn`, `rect`, `cache_images`, and `evolve`

### Evaluation planning

Key choices:

- checkpoint path(s)
- `val`, `test`, or `study`
- confidence and IoU thresholds
- `save_json` and `save_txt`
- `augment`, `merge`, and `single_cls`

### Inference planning

Key choices:

- source type: file, folder, glob, webcam, RTSP/HTTP stream, or list file
- output folder
- confidence and IoU thresholds
- `view_img`, `save_txt`, `classes`, `agnostic_nms`, `augment`, and `update`

### Export planning

Key choices:

- weights path and input size
- TorchScript, ONNX, or CoreML target
- optional backend availability for ONNX/CoreML
- whether the environment can load a fused model and trace/export it

## Parser and model smoke checks

- The CLI helper is the fastest way to confirm that the workflow parsers still import.
- The model-forward helper is the fastest way to confirm that the installed model stack can build and run a synthetic input.

## Good defaults

- Prefer the smallest validation step that proves the workflow is wired correctly.
- Only move on to full training, evaluation, or export after the relevant preflight helper passes.
- When the data or backend is uncertain, keep the inspection helper in the loop and do not jump straight to a long run.
