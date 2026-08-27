# DAMO-YOLO deployment CLI reference

The source converter parser and the bundled `export_onnx_safe.py` share the same conceptual options. Prefer the bundled helper for ONNX export from an installed `damo` package; use source-equivalent TensorRT commands only in environments where the approved TensorRT stack is installed.

## Bundled ONNX exporter flags

| Flag | Meaning | Notes |
|---|---|---|
| `-f, --config-file` | DAMO-YOLO Python config. | Must match checkpoint architecture/classes. |
| `-c, --ckpt` | PyTorch checkpoint. | Source expects a dict with `model` or a compatible raw state dict. |
| `--workdir` | Directory for config-relative reads. | Needed when config reads TinyNAS text files or relative assets. |
| `--output` | Output ONNX path. | Parent directory is created if missing. |
| `--benchmark` | Disable head postprocess before export. | Mirrors source `config.model.head.export_with_post = False`. |
| `--batch-size` | Dummy input batch and graph batch. | Keep aligned with deployment target. |
| `--img-size` | Square dummy input size. | The README uses 640 for standard models, 416 for nano/light models. |
| `--input` | ONNX input node name. | Source default is `images`. |
| `--raw-output` | Output node name for non-end2end export. | Source default is `output`. |
| `--opset` | ONNX opset. | Source default is 11; partial quantization source uses 13. |
| `--end2end` | Wrap model with NMS output tensors. | Changes output names to `num_dets`, `det_boxes`, `det_scores`, `det_classes`. |
| `--ort` | Use ONNX Runtime NMS symbolic with `--end2end`. | Otherwise the TensorRT NMS symbolic is used. |
| `--trt-version` | Select TRT7/TRT8-style NMS symbolic. | Bundled helper defaults to 8. |
| `--with-preprocess` | Include BGR->RGB and /255 preprocessing in end-to-end graph. | Only relevant with `--end2end`. |
| `--topk-all` | Max objects in NMS wrapper. | Source default is 100. |
| `--iou-thres` | NMS IoU threshold. | Source default is 0.65. |
| `--conf-thres` | NMS score threshold. | Source default is 0.05. |
| `--device` | CUDA request such as `cuda`, `cuda:0`, `0`, or `cpu`. | If CUDA is unavailable, exporter warns and uses CPU. |
| `--no-simplify` | Skip `onnxsim.simplify`. | Use when simplifier is unavailable or changes graph incorrectly. |

## Source converter flags to recognize

When reading old notes or user commands, map these source-style flags to the bundled helper or TensorRT planning:

| Source flag | Bundled equivalent or handling |
|---|---|
| `--batch_size` | `--batch-size` |
| `--img_size` | `--img-size` |
| `--output` | `--raw-output` for output node name; bundled `--output` is file path. |
| `--mode` | Parsed in source but not the key path; target is controlled by ONNX/TensorRT flags. |
| `--trt` | Not implemented by bundled helper; build TensorRT after ONNX with an approved TensorRT toolchain. |
| `--trt_type fp32|fp16|int8` | TensorRT engine precision. INT8 requires calibration. |
| `--trt_eval` | Run TensorRT COCO evaluation after engine build; requires dataset and TensorRT stack. |
| `--benchmark` | Bundled `--benchmark`. |
| `--end2end`, `--ort`, `--with-preprocess`, `--topk-all`, `--iou-thres`, `--conf-thres` | Same conceptual meaning in bundled helper. |

## TensorRT evaluation arguments

A TensorRT evaluation workflow needs:

- A config file with the same class count and validation dataset mapping as the engine.
- A `.trt` engine file.
- `--batch_size`, `--img_size`, and `--end2end` consistent with export.
- COCO validation images/annotations and `pycocotools`.
- TensorRT Python package and CUDA runtime libraries importable in the active environment.

Because TensorRT is optional and imports at module import time in the source evaluator, run `scripts/check_deploy_env.py` before trying to inspect or execute TensorRT evaluator commands.
