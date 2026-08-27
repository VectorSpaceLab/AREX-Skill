# Configuration guide

This reference explains how to select and read MMDeploy deployment configs for conversion. It focuses on the fields that affect IR export, backend conversion, partitioning, calibration, precision, and shape profiles.

## Config selection checklist

When a user asks for conversion, confirm these items in order:

1. **Codebase**: choose the upstream library that owns the model config, such as `mmdet`, `mmseg`, `mmpretrain`, `mmocr`, `mmagic`, `mmdet3d`, `mmpose`, `mmrotate`, `mmaction`, `mmrazor`, or `mmyolo`.
2. **Task**: match the codebase task enum, for example `ObjectDetection`, `Classification`, `Segmentation`, or `TextRecognition`.
3. **Backend**: choose the deployment backend that the runtime already supports.
4. **IR type**: choose ONNX or TorchScript.
5. **Shape policy**: static or dynamic, and if dynamic, which axes/profile limits are allowed.
6. **Precision**: FP32, FP16, or INT8 where supported.
7. **Partitioning**: whether marks and partition extraction are required.
8. **Calibration**: whether calibration data or quantization helpers must be created.

## Core config sections

### `ir_config` / legacy `onnx_config`

`get_ir_config` reads `ir_config` first and falls back to the older `onnx_config` layout when needed.

Common fields:

- `type`: `onnx` or `torchscript`.
- `save_file`: output IR filename.
- `input_names` / `output_names`: exported graph tensor names.
- `input_shape`: static `[H, W]` shape used for export when dynamic axes are not required.
- `dynamic_axes`: symbolic axis mapping for dynamic export.
- `opset_version`: ONNX opset, usually 11 unless a backend needs a different value.
- `export_params`: whether to export parameters.
- `keep_initializers_as_inputs`: whether ONNX initializers are also graph inputs.
- `strip_doc_string` / `verbose` / `optimize`: export behavior details.

### `codebase_config`

Typical fields:

- `type`: codebase name, such as `mmdet` or `mmpretrain`.
- `task`: codebase task enum.
- `post_processing`: backend-independent postprocess hints used by SDK metadata and task processors.
- `module`: optional external modules imported before task processor construction.

### `backend_config`

Typical fields:

- `type`: backend name.
- `common_config`: backend-wide flags such as TensorRT `fp16_mode`, `int8_mode`, or workspace settings.
- `model_inputs`: backend-specific shape/profile description.
- `quantization_config`: backend quantization settings when supported.

### `partition_config`

Partitioning is enabled only when `apply_marks=True`.

Two forms are used:

- Explicit `partition_cfg`: a list of per-partition dictionaries.
- Predefined `type`: the codebase/task provides the mark layout.

Each explicit entry usually contains:

- `save_file`: target partition ONNX filename.
- `start`: list of `mark_name:input` or `mark_name:output` markers.
- `end`: list of `mark_name:input` or `mark_name:output` markers.
- `output_names`: extracted graph output tensor names.
- `dynamic_axes`: optional symbolic axes for the partition.

### `calib_config`

When present, this config requests calibration data creation.

Typical fields:

- `create_calib`: enable HDF5 generation.
- `calib_file`: output filename, often `calib_data.h5`.

## Static and dynamic shapes

### Static export

Use a fixed `input_shape=[H, W]` in IR config and keep backend profiles consistent with the same spatial size.

Typical signals:

- ONNX export has no dynamic spatial axes.
- TensorRT uses fixed or narrow input profiles.
- OpenVINO and similar backends can still keep the graph static.

### Dynamic export

Use `dynamic_axes` to mark flexible batch and/or spatial dimensions.

Typical patterns:

- Batch-only dynamics: axis 0 is symbolic.
- Full dynamic image geometry: axes 0, 2, and 3 are symbolic.
- TensorRT dynamic profiles still need concrete `min_shape`, `opt_shape`, and `max_shape` per named input.

### TensorRT profile example pattern

`backend_config.model_inputs` for TensorRT usually looks like a list containing one dictionary with `input_shapes` entries:

```python
backend_config = dict(
    type='tensorrt',
    common_config=dict(fp16_mode=False, max_workspace_size=1 << 30),
    model_inputs=[
        dict(
            input_shapes=dict(
                input=dict(
                    min_shape=[1, 3, 320, 320],
                    opt_shape=[1, 3, 640, 640],
                    max_shape=[1, 3, 1344, 1344]))))]
)
```

Use shapes that bracket the real inference sizes. If the input image or preprocessing output falls outside the profile, backend conversion or later inference will fail.

## Precision selection

`get_precision` resolves precision from backend config:

- TensorRT: `common_config.fp16_mode` → FP16, `common_config.int8_mode` → INT8, otherwise FP32.
- NCNN: `backend_config.precision` if set.
- Other backends default to FP32 in the inspected helper.

Do not assume the backend file extension alone tells you precision. Confirm the config.

## Supported enums

### Backend

`pytorch`, `tensorrt`, `onnxruntime`, `pplnn`, `ncnn`, `snpe`, `openvino`, `sdk`, `torchscript`, `rknn`, `ascend`, `coreml`, `tvm`, `vacc`, `default`

### Codebase

`mmdet`, `mmseg`, `mmpretrain`, `mmocr`, `mmagic`, `mmdet3d`, `mmpose`, `mmrotate`, `mmaction`, `mmrazor`, `mmyolo`

### IR

`onnx`, `torchscript`, `default`

### Task

`TextDetection`, `TextRecognition`, `Segmentation`, `SuperResolution`, `Classification`, `ObjectDetection`, `InstanceSegmentation`, `VoxelDetection`, `PoseDetection`, `RotatedDetection`, `VideoRecognition`, `ModelCompress`, `MonoDetection`

## Common configuration patterns

### Faster R-CNN TensorRT dynamic conversion

- `codebase_config.type = 'mmdet'`
- `codebase_config.task = 'ObjectDetection'`
- `ir_config.type = 'onnx'`
- `ir_config.dynamic_axes` includes input batch/height/width and output batch/num-dets axes.
- `backend_config.type = 'tensorrt'`
- `backend_config.common_config` may set `fp16_mode` or `int8_mode`.
- `backend_config.model_inputs[0].input_shapes.input` contains min/opt/max shapes.

### Partitioned ONNX conversion

- `partition_config.apply_marks = True`
- `partition_config.partition_cfg` defines each subgraph.
- Every start/end marker must correspond to a mark injected during rewriting.
- `output_names` should match the extracted subgraph outputs, including indexed outputs like `pred_maps.0` when the marked tensor is a list.

### Calibration-enabled conversion

- `calib_config.create_calib = True`
- `calib_config.calib_file` names the output HDF5 file.
- If a separate dataset config is needed, pass it with `--calib-dataset-cfg` at runtime.

## Quick validation heuristics

- If `get_backend(deploy_cfg)` returns a backend that does not match the device, the build task processor stage may fail before export.
- If `get_partition_config(deploy_cfg)` returns `None`, either the partition config is absent or `apply_marks` is not enabled.
- If `get_input_shape(deploy_cfg)` returns `None`, export is expected to rely on dynamic axes.
- If `get_calib_filename(deploy_cfg)` returns `None`, no calibration HDF5 will be created by the deploy pipeline.
