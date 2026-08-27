# Catalog selection guide

Use the bundled catalog JSON and the offline query helper to narrow a model by family, name, folder number, folder name, backend/format flags, or remarks.

The commands below use paths relative to this `references/` directory.

## Catalog fields

| Field | Meaning | How to use it |
|---|---|---|
| `no` | Numeric catalog id and folder prefix | Use when you only know the number, such as `132` for `132_YOLOX`. |
| `name` | Display name in the catalog | Use when you know the model label but not the exact folder. |
| `category` | Task family | Use this first for broad routing, such as detection, pose, segmentation, or super-resolution. |
| `directory` | Folder name, when present | Use when you know the exact directory string. Some entries have no directory. |
| `formats` | Available artifacts | Use to narrow to the runtime family you need, such as `ONNX` or `OV`. |
| `remarks` | Resolution hints, variant names, or notes | Use this to separate models with the same family or to recover input-size clues. |

## Format legend

| Flag | Meaning in this repo |
|---|---|
| `FP32` | Float32 artifact in the TensorFlow/SavedModel/TFLite family when listed. |
| `FP16` | Float16 artifact. |
| `INT8` | Integer-quantized artifact. |
| `DQ` | Dynamic range quantized artifact. |
| `TPU` | EdgeTPU-oriented artifact. |
| `WQ` | Weight-quantized artifact. |
| `OV` | OpenVINO IR. |
| `CM` | CoreML artifact. |
| `TFJS` | TensorFlow.js artifact. |
| `TF-TRT` | TensorFlow-TensorRT artifact. |
| `ONNX` | ONNX artifact. |

## Selection rules

1. Start with `category` when you know the task family.
2. Add `--format` for the target backend or artifact family.
3. Add `--contains` to narrow on remarks such as `MediaPipe`, `lightning`, `thunder`, or a resolution string.
4. Use `--number` when the only clue is the numeric prefix.
5. Use `--directory` when you know the exact folder label.
6. Use `--name` when you know the model label but not the folder.
7. Check the license gate before recommending use. The catalog is a selector, not a rights grant.

## Query helper examples

```bash
python ../../../scripts/query_model_catalog.py --category "2D/3D Hand Detection" --format ONNX
python ../../../scripts/query_model_catalog.py --format OV
python ../../../scripts/query_model_catalog.py --format OV --contains MediaPipe
python ../../../scripts/query_model_catalog.py --number 132
python ../../../scripts/query_model_catalog.py --directory 132_YOLOX
python ../../../scripts/query_model_catalog.py --name YOLOX --format ONNX --limit 5
python ../../../scripts/query_model_catalog.py --list-categories
python ../../../scripts/query_model_catalog.py --list-formats
python ../../../scripts/query_model_catalog.py --json --category "2D/3D Human/Animal Pose Estimation" --format ONNX
```

## Natural trigger mapping

| User cue | Safe starting query |
|---|---|
| `find an ONNX hand pose model` | `python ../../../scripts/query_model_catalog.py --category "2D/3D Hand Detection" --format ONNX --contains hand` |
| `which models are available for OpenVINO?` | `python ../../../scripts/query_model_catalog.py --format OV` |
| `what does TPU/OV/DQ mean in this repo?` | `python ../../../scripts/query_model_catalog.py --list-formats` |
| `I only know folder 132_YOLOX` | `python ../../../scripts/query_model_catalog.py --directory 132_YOLOX` or `--number 132` |

## How to read the result

- If `directory` is present, it is the folder to inspect or pass onward.
- If `directory` is missing, keep the `no` and `name` pair and route by catalog id.
- If `remarks` contains sizes like `256x320` or `112x112`, treat them as input-shape hints.
- If `remarks` contains terms like `MediaPipe`, `SinglePose`, `lightning`, or `2D+3D`, treat them as selection hints, not full runtime guarantees.
- `OV` is not `ONNX`, and `TF-TRT` is not a generic TensorRT engine. Choose the artifact family that matches the downstream runtime.
