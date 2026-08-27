# ScaledYOLOv4 bundled runtime mirror

This directory is packaged inside the generated `scaled-yolov4` repo skill so helpers can run concrete ScaledYOLOv4 entrypoints without requiring the original checkout.

It contains the source entrypoints, model modules, utility modules, model YAMLs, dataset/hyperparameter YAMLs, and a tiny demo image/label fixture used for self-contained smoke checks.

Use the wrapper scripts in the skill tree rather than invoking these files manually when possible:

- `../scripts/run_runtime_entrypoint.py`
- `../sub-skills/training/scripts/run_training.py`
- `../sub-skills/evaluation/scripts/run_evaluation.py`
- `../sub-skills/inference/scripts/run_detection.py`
- `../sub-skills/export/scripts/run_export.py`
