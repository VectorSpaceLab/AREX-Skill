# Routing Map

## Primary Routes

| User request | First sub-skill | Then hand off when |
| --- | --- | --- |
| Dataset YAML, class names, labels, config keys, CLI arg translation | `data-and-configuration` | The user is ready to train, validate, predict, export, or track |
| Train, val, resume, tune, metrics, trainer/validator | `training-and-validation` | Dataset layout is unclear or model family is undecided |
| Predict, source handling, streaming, `Results` extraction | `inference-and-results` | The user needs exported runtime formats or model-family selection |
| Export, benchmark, ONNX/OpenVINO/TensorRT/CoreML/TFLite/Triton | `export-and-deployment` | The user needs postprocessing semantics from `Results` or backend install checks |
| Track IDs, tracker YAMLs, ReID, object counting, heatmaps, region/speed/queue solutions | `tracking-and-solutions` | The user needs detection/segmentation result fields or solutions optional extras |
| Choose YOLO/YOLOWorld/YOLOE/NAS/SAM/FastSAM/RTDETR or detect/segment/semantic/classify/pose/OBB | `model-families-and-tasks` | The user then wants train/predict/export execution details |
| Modify this repo, select tests, update docs, check style/CI, choose dev extras | `repo-development` | The code change touches a public workflow that needs semantic guidance from another sub-skill |

## Ordered Handoffs

- For a new training project: `model-families-and-tasks` → `data-and-configuration` → `training-and-validation`.
- For inference app code: `model-families-and-tasks` → `inference-and-results`; add `export-and-deployment` only when deploying outside PyTorch.
- For video analytics: `model-families-and-tasks` → `tracking-and-solutions`; add `inference-and-results` when custom post-processing consumes `Results`.
- For model export after training: `training-and-validation` → `export-and-deployment`; add `inference-and-results` for validating output semantics.
- For repo edits: start with `repo-development`, then use the user-facing workflow sub-skill for behavior-specific constraints.

## Ambiguous Requests

- `semantic` means dense semantic segmentation, not instance segmentation. Route to `model-families-and-tasks` first, then `inference-and-results` or `training-and-validation`.
- `solutions` means Ultralytics analytics apps and `yolo solutions`, not generic solution design. Route to `tracking-and-solutions`.
- `benchmark` is an Ultralytics mode tied to export/deployment formats, so route to `export-and-deployment`.
- `tune` is a Python API workflow through `model.tune()` and training infrastructure; route to `training-and-validation`.
- `exported ONNX output parsing` usually needs both `export-and-deployment` and `inference-and-results` because export handles format/backend while inference covers result semantics.

## Safety Policy

Prefer helper scripts and dry plans before running workflows that download weights/data, open streams, create runs, write media, export models, start servers, or train. Run original repo tests/examples only as verification after classifying them as safe for the current environment.
