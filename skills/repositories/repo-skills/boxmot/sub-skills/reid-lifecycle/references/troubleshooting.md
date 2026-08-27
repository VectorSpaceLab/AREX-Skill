# ReID Troubleshooting

## `train` says `--data-dir` is required

Training needs a dataset root unless the value can be inferred from `--resume` or dataset YAML specs. Pass `--data-dir` or use one or more `--data` YAML files.

## Dataset alias not found

Check the dataset name against the registry. Common aliases include `market1501`, `duke`, `dukemtmcreid`, `cuhk03`, `msmt17`, `msmt17_merged`, `veri`, and `veri776`.

## Checkpoint architecture cannot be determined

`eval-reid` can infer the model from checkpoint metadata or filename. If that fails, pass `--model` explicitly.

## Preprocess or embedding mismatch

If metrics differ unexpectedly, check these values across train/eval/export:

- `--preprocess`
- `--imgsz`
- `--inference-feature`
- `--flip-tta`

CSL-TinyViT checkpoints often require the correct inference feature mode.

## `compare-reid` target errors

Targets must be `DATASET=DATA_DIR` or `DATASET:DATA_DIR`, and the data directory must exist. Repeat `--target` for multiple datasets.

## Export dependency failures

Install only the extras needed for the requested formats:

- `onnx` for ONNX export
- `openvino` for OpenVINO export
- `tflite` for TFLite export

TensorRT export is a GPU-specific path; a Python package install does not replace the required NVIDIA runtime stack.

## Empty embedding output

If `ReIDModel.embed(...)` returns empty arrays, check whether boxes are empty or invalid. OBB boxes are converted to enclosing AABBs for crop extraction when needed.
