# Deployment Conversion Guide

This reference covers deployment-oriented workflows only: exporting ONNX, preparing TensorRT/RKNN/MMDeploy configs, running backend-artifact inference, and diagnosing backend readiness. The self-contained runtime route favors installed package commands, MMDeploy tooling, and bundled dependency checks; MMYOLO source-project EasyDeploy scripts are evidence/reference material, not required runtime files.

## Quick route chooser

| Request shape | Best path |
| --- | --- |
| CPU ONNXRuntime export or inference | Use MMDeploy with an ONNXRuntime deploy config, or use a user-supplied EasyDeploy project only if the caller explicitly provides it. |
| TensorRT engine build | Require TensorRT + CUDA + NVIDIA GPU; use MMDeploy TensorRT configs or a user-supplied EasyDeploy project. |
| RKNN deployment | Use RKNN deploy configs and vendor toolchain; expect target-platform-specific constraints. |
| MMDeploy backend inference or evaluation | Use MMDeploy deploy/test APIs or tools with an MMYOLO model config and backend artifact. |
| Upstream checkpoint key conversion | Use package-level `mim run mmyolo model_converters:<converter>` commands from [model converters](model-converters.md). |

## Backend/export concepts

MMYOLO deployment flows have four moving parts:

1. **Model config**: the MMEngine `.py` config for the training/inference model.
2. **Checkpoint**: the `.pth` weights matching the model config and class count.
3. **Deploy config**: a backend-specific config for ONNXRuntime, TensorRT, RKNN, INT8, static shape, or dynamic shape.
4. **Backend artifact**: the exported ONNX/model/engine/directory consumed by a runtime.

Do not start export/build work until all four are known or intentionally selected.

## Export option meanings

Most MMYOLO/EasyDeploy/MMDeploy export commands expose variants of these options:

| Option | Meaning |
| --- | --- |
| model config / checkpoint | Model definition and trained weights. |
| output/work directory | Export output directory. |
| input shape / image size | Static height/width or dynamic min/opt/max range. |
| batch size | Export-time batch dimension. |
| device | `cpu` for ONNXRuntime export where supported; `cuda:0` for TensorRT and many GPU builds. |
| simplify | Optional ONNX simplification when `onnxsim` is installed. |
| opset | ONNX opset version; keep compatible with the target runtime. |
| backend | ONNXRuntime, TensorRT, RKNN, or another vendor backend. |
| pre-top-k / keep-top-k / score / IoU | Postprocess threshold settings for end-to-end detection export. |
| model-only | Export backbone/head output without embedded decode/NMS postprocess; downstream runtime must handle decode/NMS. |

## Backend meaning

| Backend | Meaning | CPU substitute |
| --- | --- | --- |
| ONNXRuntime | ONNX model for CPU or CUDA ONNXRuntime inference. | CPU is a full route for many inference checks. |
| TensorRT | NVIDIA TensorRT engine or TensorRT-targeted ONNX. | None for engine build/runtime. |
| RKNN | Rockchip RKNN toolchain/runtime. | None for vendor deployment. |
| DeepStream | NVIDIA DeepStream pipeline consuming TensorRT artifacts. | None. |
| MMDeploy SDK/runtime | MMDeploy backend model directory and SDK/runtime wrappers. | Depends on backend; ONNXRuntime can be CPU. |

If the target backend package or hardware is missing, stop early and switch to a CPU ONNXRuntime plan or a vendor-enabled environment before retrying.

## MMDeploy config basics

MMYOLO deploy configs are organized around static/dynamic input shape and backend type. In a package installation, use MIM/package resources or user-supplied config copies rather than assuming the original repository checkout is available.

| File family | Key fields | Use |
| --- | --- | --- |
| `base_static.py` | `onnx_config`, `codebase_config`, `post_processing`, `module=['mmyolo.deploy']` | Static end-to-end export. |
| `base_dynamic.py` | Dynamic axes for input batch/height/width and outputs | Dynamic end-to-end export. |
| `detection_onnxruntime_static.py` / `detection_onnxruntime_dynamic.py` | `backend_config=dict(type='onnxruntime')` | ONNXRuntime deployment. |
| `detection_tensorrt_static-640x640.py` | `onnx_config.input_shape`, `backend_config.type='tensorrt'`, `common_config.fp16_mode`, `max_workspace_size` | TensorRT static deployment. |
| `detection_tensorrt_dynamic-192x192-960x960.py` | `model_inputs.input_shapes` with min/opt/max shapes | TensorRT dynamic deployment. |
| `detection_tensorrt-fp16_*` | `fp16_mode=True` | TensorRT FP16 variants. |
| `detection_tensorrt-int8_*` | `int8_mode=True`, `calib_config` | TensorRT INT8 variants. |
| `detection_rknn-fp16_static-320x320.py` / `detection_rknn-int8_static-320x320.py` | `backend_config.type='rknn'`, `target_platform`, `input_size_list` | RKNN deployment templates. |

Config fields that matter:

- `onnx_config.input_shape` controls static ONNX export.
- `onnx_config.dynamic_axes` controls dynamic ONNX export.
- `codebase_config.post_processing` sets pre-top-k, keep-top-k, IoU, and score thresholds.
- `use_efficientnms` switches the TensorRT path to the EfficientNMS plugin when supported.
- `calib_config` is required for INT8 calibration flows.
- RKNN configs stay narrow and target a specific platform and input size.

Static model-config templates disable resizing tricks that would change the exported tensor shape, commonly by using `LetterResize(..., allow_scale_up=False, use_mini_pad=False)` and `batch_shapes_cfg=None`. Dynamic templates preserve dynamic sizing.

## MMDeploy export, inference, and evaluation route

Use MMDeploy's installed tools/APIs with:

- `DEPLOY_CFG`: backend deploy config.
- `MODEL_CFG`: MMYOLO model config.
- `CHECKPOINT`: trained checkpoint.
- `IMG`: representative input image for tracing/visualization.
- `OUTPUT_DIR`: deploy work directory.
- `BACKEND_MODEL`: generated ONNX/engine/backend model artifact or directory.

Template shape:

```shell
# Replace `mmdeploy-deploy-tool` and `mmdeploy-test-tool` with the command form provided by the installed MMDeploy version.
mmdeploy-deploy-tool DEPLOY_CFG MODEL_CFG CHECKPOINT IMG --work-dir OUTPUT_DIR --device cpu --dump-info
mmdeploy-test-tool DEPLOY_CFG MODEL_CFG --model BACKEND_MODEL --device cpu --work-dir OUTPUT_DIR
```

Use `cuda:0` for TensorRT deployment and testing. Use `cpu` for ONNXRuntime. Before proposing a concrete command, run the bundled dependency checker and inspect the installed MMDeploy version's command help.

MMDeploy backend inference flow:

1. Load deploy config and model config.
2. Build a task processor for the selected backend/device.
3. Build the backend model from deployed artifacts.
4. Create inputs with the deployment input shape.
5. Run backend inference and visualize or evaluate results.

The MMDeploy SDK route uses a deployed model directory rather than a plain training checkpoint.

## EasyDeploy evidence and boundary

MMYOLO v0.6.0 includes an EasyDeploy project in the source repository, but those project scripts are not bundled into this self-contained skill and may not exist in a package-only environment. Treat EasyDeploy-specific commands as **reference-only** unless the caller explicitly provides an EasyDeploy project checkout or a package exposing those commands.

When a caller does provide EasyDeploy tooling, check these facts before using it:

- ONNXRuntime export can usually run on CPU when `onnx` is installed; `onnxsim` is optional.
- TensorRT export/build requires CUDA, TensorRT Python bindings, and an NVIDIA GPU.
- End-to-end export embeds decode/NMS postprocess when the backend supports it.
- Model-only export skips postprocess; downstream runtime must decode and run NMS.
- TensorRT engine build needs min/opt/max shape choices; a static engine can use identical shapes.
- RKNN paths are target-platform-specific and may use model-only fallback.

## MMYOLO deploy integration points

- `mmyolo.deploy.object_detection` registers the MMYOLO codebase with MMDeploy.
- The visualizer pulls dataset metainfo from the model config when available.
- MMDeploy's PyTorch-model build path loads the training checkpoint, reverts sync batch norm, switches the model to deploy mode, and moves it to the requested device.
- The YOLOv5 head rewriter chooses `multiclass_nms` or `efficient_nms` according to the deploy config.
- The RKNN rewriter path returns raw outputs instead of the normal postprocess path.

## Optional dependencies and hardware gates

| Workflow | Required gate |
| --- | --- |
| ONNX export | `onnx`; `onnxsim` optional for simplify. |
| ONNXRuntime inference | `onnxruntime`; CPU is enough for the common path. |
| TensorRT engine build or engine inference | `tensorrt` + NVIDIA CUDA + compatible GPU. |
| RKNN deployment | RKNN toolchain and target hardware. |
| MMDeploy backend inference | `mmdeploy`; `mmdeploy_runtime` if SDK inference is needed. |
| DeepStream | NVIDIA driver, CUDA, DeepStream SDK, and TensorRT engine. |

CPU-only inspection can confirm only package presence. It cannot verify TensorRT, RKNN, or DeepStream conversion without the vendor stack and hardware.

## Useful recovery rule

If the backend package or required hardware is missing, stop the deployment path early and switch to a CPU ONNXRuntime plan or a vendor-enabled environment before trying again. Use [`../scripts/check_deployment_dependencies.py`](../scripts/check_deployment_dependencies.py) before proposing export/build commands.
