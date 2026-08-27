# Conversion workflows

This reference explains how to run MMDeploy model conversion from user-provided inputs. It assumes the Python environment can import `mmdeploy`, the target OpenMMLab codebase, PyTorch, MMCV/MMEngine, ONNX, and the selected backend runtime. If the backend itself is missing or misconfigured, stop this workflow at the backend handoff and use backend guidance.

## Required inputs

| Input | Purpose | Checks before running |
|---|---|---|
| `deploy_cfg` | MMDeploy deployment config selecting codebase, task, IR, backend, shape, precision, partition, and calibration behavior. | It should match the model task and target backend. See `configuration.md` for fields and enums. |
| `model_cfg` | Upstream OpenMMLab model config used to build the PyTorch model and data pipeline. | The owning codebase package must be importable and version-compatible with the config. |
| `checkpoint` | PyTorch checkpoint path or supported URL. | It must belong to the selected `model_cfg`; mismatched heads/classes usually fail during model loading or later validation. |
| `img` | Representative image/data path used to create model inputs during export and default visualization. | Use a real sample that exercises the intended preprocessing and stays inside the static/dynamic profile. |
| `--work-dir` | Destination for IR, backend files, SDK metadata, calibration data, and visualizations. | Prefer an empty per-run directory. |
| `--device` | Conversion and visualization device. | Use `cuda:0` for TensorRT; use `cpu` for CPU backends such as OpenVINO/ONNXRuntime CPU. |

## Main CLI

Use the bundled conversion script:

```bash
python <conversion-skill>/scripts/deploy.py \
  DEPLOY_CFG \
  MODEL_CFG \
  CHECKPOINT \
  INPUT_IMG \
  --work-dir WORK_DIR \
  --device DEVICE \
  --log-level INFO
```

Add options only when needed:

| Option | Effect | Notes |
|---|---|---|
| `--test-img IMG [IMG ...]` | Image(s) for final backend/PyTorch visualization. | Defaults to the conversion `img`. Use this when the export dummy input and desired visual check differ. |
| `--dump-info` | Writes SDK metadata into the work directory. | Produces `deploy.json`, `pipeline.json`, and `detail.json` before conversion finishes. SDK runtime use is a separate handoff. |
| `--show` | Attempts to display rendered visualization windows. | In headless sessions the API falls back to saving/omitting display; prefer output files in unattended runs. |
| `--calib-dataset-cfg CFG` | Uses another dataset config for calibration data. | Only affects calibration HDF5 creation when the deploy config asks to create calibration data. |
| `--quant` | Enables the NCNN int8 quantization path after NCNN backend conversion. | Requires NCNN backend files plus PPQ; use with `--quant-image-dir` when a flat representative image directory is available. |
| `--quant-image-dir DIR` | Flat image folder for NCNN quantization calibration. | Images should be representative real data, not a test/accuracy set. |
| `--uri HOST:PORT` | Remote endpoint for edge-device inference paths such as SNPE. | Backend-specific; not needed for ordinary local CPU/GPU conversion. |

## End-to-end pipeline stages

`scripts/deploy.py` performs these stages in order:

1. Load `deploy_cfg` and `model_cfg`, create `--work-dir`, and optionally dump SDK metadata.
2. Read `ir_config` (or legacy `onnx_config`) and export PyTorch to the configured IR with `torch2onnx` or `torch2torchscript`.
3. If `partition_config.apply_marks=True`, extract one or more partition ONNX files from the exported ONNX model using mark names in `partition_config`.
4. If `calib_config.create_calib=True`, create the calibration HDF5 file named by `calib_config.calib_file` or the default filename.
5. Convert IR files to the target backend through `to_backend`; TensorRT backend conversion is run through the multiprocessing pipeline.
6. Apply backend-specific quantization helpers: VACC int8 dataset generation, or NCNN PPQ quant table generation followed by NCNN int8 conversion when `--quant` is set.
7. Run `visualize_model` for backend files and then for the original PyTorch checkpoint, saving `output_<backend>.jpg` and `output_pytorch.jpg` when visualization succeeds.

A failure in stage 5 or later usually means the IR was created but backend/runtime dependencies, dynamic profile, or backend input files need attention.

## Faster R-CNN to TensorRT dynamic shape with SDK dump

For object detection with a TensorRT dynamic deploy config, provide all required paths and use a CUDA device:

```bash
python <conversion-skill>/scripts/deploy.py \
  DEPLOY_CFG_FOR_MMDET_FASTER_RCNN_TENSORRT_DYNAMIC \
  MODEL_CFG_FOR_FASTER_RCNN \
  CHECKPOINT_FOR_THE_MODEL_CFG \
  REPRESENTATIVE_DETECTION_IMAGE \
  --work-dir work_dirs/faster-rcnn-trt-dynamic \
  --device cuda:0 \
  --dump-info \
  --test-img REPRESENTATIVE_DETECTION_IMAGE
```

Use a deploy config for MMDetection object detection, TensorRT backend, and dynamic shape; such configs are commonly named with a pattern like `detection_tensorrt_dynamic-<minHxW>-<maxHxW>.py`. The model config, checkpoint, and image paths come from the user's upstream MMDetection workspace or package installation.

Expected artifact signals in `work_dirs/faster-rcnn-trt-dynamic/`:

- IR export: usually `end2end.onnx` unless the deploy config names another `save_file`.
- Backend engine: usually `end2end.engine` for TensorRT.
- SDK metadata from `--dump-info`: `deploy.json`, `pipeline.json`, `detail.json`.
- Visual comparisons: `output_tensorrt.jpg` and `output_pytorch.jpg` if both visualization calls complete.

If TensorRT reports an input dimension outside the optimization profile, update the deploy config `backend_config.model_inputs[].input_shapes` so `min_shape <= actual NCHW <= max_shape` and `opt_shape` is representative.

## Work-dir artifact map

| Artifact | Created by | Meaning |
|---|---|---|
| `end2end.onnx` or configured `*.onnx` | `torch2onnx` | ONNX IR before backend conversion. If partitioning is enabled, this may be the source for extracted subgraphs. |
| `*.pt` / TorchScript save file | `torch2torchscript` | TorchScript IR when `ir_config.type='torchscript'`. |
| Partition `*.onnx` files | `extract_model` | Extracted ONNX subgraphs named by each `partition_config.partition_cfg[].save_file`. |
| `calib_data.h5` or configured calibration filename | `create_calib_input_data` or VACC helper | Calibration tensors for int8/PTQ workflows. End-to-end configs contain `calib_data/end2end/input/...`; partition configs contain `calib_data/partition0/...`, `partition1`, etc. |
| `*.engine` | TensorRT backend manager | TensorRT engine file. Requires compatible CUDA/TensorRT runtime to build and later infer. |
| `*.param` and `*.bin` | NCNN backend manager | NCNN network and weight files. With `--quant`, int8 variants are generated after PPQ quant table creation. |
| `*.xml` and `*.bin` | OpenVINO backend manager | OpenVINO model files. |
| `*.json` | PPLNN or TVM metadata | Backend-specific algorithm or weight/input/output metadata. |
| `*.rknn`, `*.om`, `*.mlpackage`, `*.dlc` | RKNN, Ascend, CoreML, SNPE managers | Vendor backend artifacts. Runtime/device availability is backend-owned. |
| `deploy.json` | `--dump-info` | SDK model inventory: MMDeploy version, task class, backend model names, precision, batch/dynamic flags, and customs. |
| `pipeline.json` | `--dump-info` | SDK preprocessing, inference, and postprocessing graph. |
| `detail.json` | `--dump-info` | Codebase, checkpoint path as supplied, codebase config, IR config, backend config, and calibration config. |
| `output_<backend>.jpg`, `output_pytorch.jpg` | `visualize_model` | Rendered smoke outputs from backend files and original checkpoint. Absence can indicate visualization/runtime failure even when conversion artifacts exist. |

## ONNX and TorchScript export without full CLI orchestration

Prefer `scripts/deploy.py` for normal user conversions because it also handles partitioning, backend conversion, SDK dump, calibration, and visualization. For programmatic workflows, use the package APIs in `api-reference.md`:

- `torch2onnx(...)` for ONNX IR export.
- `torch2torchscript(...)` for TorchScript IR export.
- `extract_model(...)` for mark-based ONNX partitioning after export.
- `to_backend(...)` for backend conversion from existing IR files.

The standalone source utilities for ONNX export and ONNX partition extraction are intentionally not bundled because the deploy CLI and public APIs cover the selected runtime path with less duplication.

## Partition workflow

Partitioning requires both marked nodes in the exported ONNX graph and a deploy config that enables marks:

```python
partition_config = dict(
    type='custom_partition',
    apply_marks=True,
    partition_cfg=[
        dict(
            save_file='part0.onnx',
            start=['detector_forward:input'],
            end=['yolo_head:input'],
            output_names=['pred_maps.0', 'pred_maps.1', 'pred_maps.2'])
    ])
```

Rules:

- `apply_marks=True` is required; otherwise `get_partition_config` returns `None` and no extraction runs.
- Each `start` and `end` item uses `mark_name:input` or `mark_name:output`. The mark name comes from the `@mark(name, inputs=[...], outputs=[...])` wrapper used during rewriting.
- If a marked tensor is a list/tuple, the ONNX mark names may be indexed, such as `pred_maps.0`, `pred_maps.1`, `pred_maps.2`.
- A config can provide explicit `partition_cfg` entries or a predefined `type`. Predefined partition lookup is codebase/task-specific and is documented in the API as currently centered on MMDetection.
- `dynamic_axes` can be supplied per partition when output/input names differ from the end-to-end graph.

## Calibration and quantization workflow

Calibration is controlled by deploy config and CLI options:

```python
calib_config = dict(create_calib=True, calib_file='calib_data.h5')
```

- When `create_calib=True`, `scripts/deploy.py` writes the calibration HDF5 before backend conversion. If `--calib-dataset-cfg` is absent, it uses the validation dataloader from `model_cfg`; otherwise it loads the supplied dataset config.
- The calibration dataloader is forced to batch size 1 by the API. Make sure the dataset config has a usable `val_dataloader` (or equivalent for the selected `dataset_type='val'`).
- NCNN PTQ uses `--quant` and optionally `--quant-image-dir`; the flat image directory path is consumed by `scripts/onnx2ncnn_quant_table.py` through `QuantizationImageDataset`.
- VACC int8 conversion reads `backend_config.model_inputs[].qconfig.dtype`. When it is `int8`, `scripts/deploy.py` calls `scripts/onnx2vacc_quant_dataset.py` to write `calib_data.h5`.
- Do not calibrate on held-out test data. Use representative training/validation-style samples from the deployment domain.

## Bundled source-script decisions

| Runtime path | Bundled file | Decision | Reason |
|---|---|---|---|
| End-to-end conversion | `scripts/deploy.py` | copied/adapted | It is the main orchestrator for IR export, partitioning, calibration, backend conversion, SDK dump, quantization hooks, and visualization. |
| NCNN quant table | `scripts/onnx2ncnn_quant_table.py` | copied/adapted | It is called by `deploy.py` for NCNN int8 and is useful as a direct helper; required CLI options were made explicit. |
| VACC quant dataset | `scripts/onnx2vacc_quant_dataset.py` | copied/adapted | It is called by `deploy.py` for VACC int8; unsafe string evaluation was replaced with literal parsing. |
| NCNN image dataset | `scripts/quant_image_dataset.py` | copied/adapted | It is a helper imported by the NCNN quant table script. |
| Standalone ONNX export utility | not bundled | reference-only | The deployed `scripts/deploy.py` and `torch2onnx` API already cover ONNX export with the selected conversion path. |
| Standalone ONNX extraction utility | not bundled | reference-only | The deployed `scripts/deploy.py` and `extract_model` API already cover mark-based extraction. |
| Standalone backend converters | not bundled here | reference-only / backend-owned | Backend conversion is routed through `to_backend` inside `deploy.py`; backend-specific installation/runtime failures are handled outside this conversion sub-skill. |
