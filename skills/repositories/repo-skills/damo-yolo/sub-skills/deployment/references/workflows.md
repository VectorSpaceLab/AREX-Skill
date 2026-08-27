# DAMO-YOLO deployment workflows

DAMO-YOLO deployment starts from a trained PyTorch detector checkpoint plus the matching Python config. The source converter supports ONNX export, optional end-to-end NMS export, TensorRT engine build, and optional TensorRT evaluation. This generated sub-skill bundles a safe ONNX exporter and documents TensorRT/quantization paths without pretending that optional backend stacks are always available.

## Choose the deployment target

| Target | Use when | Required dependencies | Notes |
|---|---|---|---|
| Raw ONNX | Need portable graph, ONNX Runtime preprocessing elsewhere, or latency benchmark without postprocess. | `damo`, PyTorch, `onnx`; optionally `onnxsim`. | Use `--benchmark` to disable head postprocess. |
| ONNX with ONNX Runtime NMS | Need an ONNX Runtime graph with NMS included. | Raw ONNX deps plus runtime that supports NonMaxSuppression. | Use `--end2end --ort`. |
| ONNX with TensorRT NMS plugin | Need an ONNX graph intended for TensorRT parsing. | Raw ONNX deps plus TensorRT-compatible parser/runtime downstream. | Use `--end2end` and set TRT version expectation. |
| TensorRT FP32/FP16 engine | Need NVIDIA GPU deployment engine. | TensorRT Python package and libraries, CUDA runtime, compatible PyTorch. | Source converter builds `.trt` after ONNX when `--trt` is set. |
| TensorRT INT8 / partial quantization | Need INT8 latency with selected full-precision layers. | TensorRT, CUDA/PyCUDA, `pytorch_quantization`, calibration images. | Expensive and data-dependent; not verified without calibration data/backend stack. |
| OpenVINO CPU benchmark | Need Intel CPU latency measurement from ONNX. | OpenVINO model optimizer / benchmark app. | README converts ONNX to OpenVINO IR outside DAMO-YOLO Python. |

## Safe ONNX export with bundled helper

Use this when you want a generated-skill-owned command that imports the installed `damo` package rather than a repo-local converter script.

```bash
sub-skills/deployment/scripts/export_onnx_safe.py \
  -f /path/to/damoyolo_config.py \
  -c /path/to/damoyolo_checkpoint.pth \
  --workdir /path/used/by/config-relative-assets \
  --output /path/to/damoyolo.onnx \
  --batch-size 1 \
  --img-size 640 \
  --device cuda
```

For latency-only export without postprocess:

```bash
sub-skills/deployment/scripts/export_onnx_safe.py \
  -f /path/to/damoyolo_config.py \
  -c /path/to/damoyolo_checkpoint.pth \
  --output /path/to/damoyolo_benchmark.onnx \
  --batch-size 1 --img-size 640 --benchmark --device cuda
```

For ONNX Runtime NMS export:

```bash
sub-skills/deployment/scripts/export_onnx_safe.py \
  -f /path/to/damoyolo_config.py \
  -c /path/to/damoyolo_checkpoint.pth \
  --output /path/to/damoyolo_end2end_ort.onnx \
  --batch-size 1 --img-size 640 \
  --end2end --ort --topk-all 100 --iou-thres 0.65 --conf-thres 0.05
```

## TensorRT engine build and evaluation

The generated `export_onnx_safe.py` intentionally stops at ONNX. The legacy converter path continues from there into TensorRT when `--trt` is set. Preserve the same conceptual arguments when you hand off to an approved TensorRT toolchain:

- config file and checkpoint path
- `--batch_size` / `--img_size`
- `--trt` to request engine build
- `--trt_type fp32|fp16|int8`
- `--end2end` when NMS should be inside the engine
- `--trt_eval` when you want an immediate COCO evaluation pass

For TensorRT evaluation, use the deployment CLI reference to mirror the source evaluation arguments: config, `.trt` file, batch size, image size, and `--end2end` if NMS is inside the engine.

## Partial INT8 quantization

The source partial-quantization workflow quantizes only selected operations for `tiny`, `small`, or `medium` model types. It uses `pytorch_quantization` to collect calibration statistics, saves calibrated weights, exports ONNX, then builds a TensorRT INT8 engine.

Use this path only when:

- A TensorRT-compatible NVIDIA GPU environment is already available.
- Calibration images are present and representative.
- The user accepts calibration/runtime cost.
- The chosen model type is one of `tiny`, `small`, or `medium`.

Preserve the legacy command intent by keeping the same core flags:

- config file and checkpoint path
- `--batch_size` / `--img_size`
- `--trt` and `--trt_eval`
- `--model_type tiny|small|medium`

Do not run this as a quick smoke test. Use [Deployment troubleshooting](troubleshooting.md) to diagnose missing TensorRT, calibration, or path issues first.
