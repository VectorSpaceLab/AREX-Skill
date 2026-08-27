# Deployment and Inference Guide

This guide distills the deployment surface from the anomalib source tree:

- `src/anomalib/deploy/*`
- `src/anomalib/models/components/base/export_mixin/*`
- `docs/source/markdown/guides/reference/deploy/index.md`
- `docs/source/markdown/get_started/anomalib.md`
- `examples/api/01_getting_started/*`
- `tools/inference/*`
- `tests/unit/deploy/*`
- `tests/integration/tools/*`

## End-to-end path

1. Train or load a model.
2. Export it with `Engine.export(...)` or a direct `ExportMixin` method.
3. Choose a runtime path:
   - `Engine.predict(...)` when staying inside Lightning.
   - `TorchInferencer` for a trusted Torch checkpoint.
   - `OpenVINOInferencer` for an exported deployment artifact.
4. Render, save, or post-process the predictions.

## Choose the right runtime

| Situation | Best path | Why |
| --- | --- | --- |
| You already have an `AnomalibModule` and want Lightning-managed prediction | `Engine.predict(...)` | Handles datasets, datamodules, `data_path`, and validation hooks. |
| You have a trusted Torch checkpoint and need direct replay | `TorchInferencer` | Minimal path, but it is legacy and pickle-based. |
| You have ONNX or OpenVINO artifacts for deployment | `OpenVINOInferencer` | Runs optimized inference and returns numpy-backed batches. |
| You need a quick export artifact | `Engine.export(...)` | Dispatches to Torch, ONNX, or OpenVINO export helpers. |

## Engine.predict input variants

| Variant | Example shape | Behavior |
| --- | --- | --- |
| `dataset` | `dataset=PredictDataset(...)` or any `Dataset` | Wrapped in a `DataLoader` with the dataset's `collate_fn`. |
| `datamodule` | `datamodule=...` | Uses Lightning's prediction hooks and dataloaders. |
| `data_path` | `data_path="path/to/images"` | Builds a `PredictDataset` from the path. |
| `dataloaders` | `dataloaders=[loader]` or `DataLoader(...)` | Uses explicit loaders without wrapping a dataset. |

## Export formats and compression

| Export type | Output path | Notes |
| --- | --- | --- |
| `torch` | `weights/torch/model.pt` | Saves `{"model": self}` with `torch.save`; only trust the file if you trust the source. |
| `onnx` | `weights/onnx/model.onnx` | `dynamo=True` requires `onnxscript`; the legacy exporter path is still available with `dynamo=False`. |
| `openvino` | `weights/openvino/model.xml` + `.bin` | Supports OpenVINO conversion and optional NNCF compression. |

### OpenVINO compression options

| Compression | Needs datamodule? | Notes |
| --- | --- | --- |
| `FP16` | No | Good default when you only need a deployed IR model. |
| `INT8` | No | Weight compression only. |
| `INT8_PTQ` | Yes | Calibrates with the datamodule validation loader. |
| `INT8_ACQ` | Yes | Accuracy-aware quantization; metric is optional and defaults to image-level F1. |

## Bundled helper scripts

| Script | Role |
| --- | --- |
| `scripts/basic-inference-api.py` | Minimal Python `Engine.predict` recipe using `PredictDataset`. |
| `scripts/basic-openvino-inference.py` | Minimal OpenVINO runtime recipe. |
| `scripts/lightning-inference.py` | CLI-style helper that wires `PredictDataset` into `Engine.predict`. |
| `scripts/openvino-inference.py` | Image-loop helper around `OpenVINOInferencer`. |
| `scripts/torch-inference.py` | Legacy Torch helper with the trust gate preserved. |

## Excluded or reference-only surfaces

- `tools/inference/gradio_inference.py` is reference-only because it launches a server and depends on optional UI packages.
- `examples/api/01_getting_started/basic_torch_inference.py` is only a header stub in this checkout.
- Training loops, benchmark orchestration, and Studio app files are outside this skill's scope.
