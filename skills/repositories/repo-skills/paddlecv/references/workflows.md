# Workflows

## 1) Single-op inference from a config file
Use this when the user wants one model family such as classification, detection, segmentation, feature extraction, or keypoint.

```bash
python skills/disco/paddlecv/scripts/run_predict.py \
  --config paddlecv/configs/single_op/PP-YOLOE+.yml \
  --input paddlecv/demo/000000014439.jpg
```

Useful flags:
- `--output-dir` to change the result folder.
- `--device` to switch between `CPU`, `GPU`, or `XPU`.
- `--run-mode` to select `paddle`, `trt_fp32`, `trt_fp16`, `trt_int8`, or `mkldnn` when the backend supports it.
- `-o KEY=VALUE` in the underlying config flow to override YAML values.

## 2) Task-name system pipeline
Use this when the user wants OCR, PP-Structure, ShiTu, Human, Vehicle, TinyPose, information extraction, sentiment analysis, or TTS.

```python
from paddlecv import PaddleCV

pipe = PaddleCV(task_name="PP-OCRv3")
result = pipe("paddlecv/demo/00056221.jpg")
```

This path is the cleanest way to use the packaged presets and the built-in `TASK_DICT` mapping.

## 3) Direct DAG control with `config_path`
Use this when the user wants a specific graph, a custom operator, or a system config that is not exposed as a `task_name`.

```python
from paddlecv import PaddleCV

pipe = PaddleCV(config_path="paddlecv/configs/system/PP-Structure-table.yml")
result = pipe("paddlecv/demo/table.jpg")
```

## 4) Catalog and smoke checks
- `scripts/smoke_import.py` verifies importability and prints the supported task/catalog summary.
- `PaddleCV.list_all_supported_tasks()` prints the packaged task names.
- `PaddleCV.list_all_supported_models(filters=[...])` prints the model catalog for one or more substring filters.

## 5) Video and directory inputs
- Directory inputs are treated as image directories and scanned for image extensions.
- Video inputs are processed frame by frame and written back to the configured output directory.
- In-memory `numpy.ndarray` inputs are accepted by the underlying pipeline when the operator graph expects them.

## 6) Custom-operator route
If the request is about `register`, `create_operators`, `BaseOp` subclasses, or `check_name` validation, switch to `sub-skills/custom-ops/SKILL.md`.

## Workflow selection tip
If the question is ambiguous, choose by the entry signal:
- `paddlecv/configs/single_op/` or model family names → `single-model-inference`
- `PaddleCV(task_name=...)`, OCR, structure, retrieval, TTS, or IE/SA tasks → `system-pipelines`
- `@register`, connectors, outputs, or config graph errors → `custom-ops`
