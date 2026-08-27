# ONNX Cross-Cutting Troubleshooting

Read this when an ONNX workflow fails before you know which sub-skill owns the detailed fix. For workflow-specific symptoms, jump to the nearest sub-skill troubleshooting reference.

## Install and Import Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'onnx.onnx_cpp2py_export'` when working inside a checkout | ONNX's C++ extension has not been built, or the source tree shadows the installed package | Use an isolated environment and install/build ONNX first. For a checkout, prefer `pixi run install`; otherwise run `python -m pip install -e . -v` from the checkout, then import from outside the checkout for sanity checks. |
| `pip check` reports protobuf/numpy/ml_dtypes conflicts | Environment already contains incompatible dependency versions | Use a fresh environment for ONNX instead of repairing a shared environment. Install only base ONNX and the optional extra actually needed. |
| Import succeeds but a CLI entry point is missing | The active shell is using a different Python environment than the package install | Run `python -m pip show onnx`, `python -m pip check`, and invoke entry points from the same environment. `check-model`, `check-node`, and `backend-test-tools` are ONNX console scripts. |
| Image-related reference tests fail with missing Pillow | Optional reference extra not installed | Install `onnx[reference]` only when image-decoder/reference workflows require it. Do not make Pillow a baseline ONNX requirement. |

## Model File and Data Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Checker complains about missing `opset_import` | IR version requires explicit imported operator sets | Add `opset_imports=[onnx.helper.make_opsetid('', <version>)]` when building models. Use the default-domain empty string for standard ONNX ops. |
| `ValidationError` mentions graph topological order, SSA, duplicate names, or undefined inputs | Nodes are not topologically sorted, an output name is reused, or a graph output/input references an undefined value | Inspect graph inputs, initializers, node inputs/outputs, and outputs. Use `validation-and-conversion` before trying to run a backend. |
| Large model validation or shape inference fails because the protobuf is too large | Single serialized protobuf exceeds ONNX's in-memory size limit | Use model path APIs (`onnx.checker.check_model(path)`, `onnx.shape_inference.infer_shapes_path`) and external data. Do not load a >2GB model into a `ModelProto` just to check it. |
| External data does not load | External tensor `location` is not relative to the model file directory, data files were moved, or unsafe up-directory paths were used | Keep external data beside the model or call `load_external_data_for_model(model, base_dir)` after loading with `load_external_data=False`. Use safe relative locations without `..`. |
| `ValueError: Unsupported format` from load/save | Serialization format was not inferred from the extension and no valid `format` was provided | Use supported formats: `protobuf`, `textproto`, `onnxtxt`, or `json`. Prefer `.onnx`/`.pb`, `.pbtxt`, `.onnxtxt`, or `.onnxjson` extensions when possible. |

## Validation, Shape, Parser, and Version Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `onnx.shape_inference.infer_shapes` raises `TypeError` for a path | `infer_shapes` accepts a `ModelProto` or bytes, not paths | Use `infer_shapes_path(model_path, output_path=...)` for file paths and large models. |
| Strict shape inference fails but non-strict returns a model | A shape conflict or unsupported inference path was encountered | Run strict mode when you need an actionable failure, then inspect the op, input types, and existing value info. Do not assume shape inference is complete for dynamic models. |
| `ParseError` from ONNX text syntax | Text model grammar differs from Python pseudo-code; attributes, graph bodies, and type syntax are strict | Use `validation-and-conversion/references/workflows.md` or `operator-spec-maintenance/references/onnx-text-syntax.md` for compact grammar patterns and body-subgraph idioms. |
| `ConvertError` or runtime error in version conversion | ONNX has no adapter for the requested op/domain/version path | Version converter mainly handles default-domain ops with registered adapters. If conversion is unsupported, keep the original opset, edit the model manually with validation, or implement an adapter for ONNX maintenance tasks. |

## Build, Test, and Generated-File Failures

- Pure Python changes take effect in editable installs, but C++ changes require rebuilding the extension.
- If `pixi` is available, prefer `pixi run install`, `pixi run pytest`, `pixi run gtest`, and `pixi run gen-all` for reproducible repo workflows.
- If using plain commands, build with `python -m pip install -e . -v`; set `ONNX_BUILD_TESTS=1` before installing when C++ gtests are needed.
- Edit `.in.proto` files, operator schemas, and source files first; then regenerate generated proto/docs artifacts. Do not hand-edit generated `*_pb2.py`, generated proto outputs, or generated operator docs as the source of truth.
- Run `lintrunner` for changed files before a coding task is complete; Python files require `from __future__ import annotations` and absolute imports from `onnx`.

## Backend and Runtime Boundaries

ONNX checker/reference utilities are not the same as a production inference runtime. If an ONNX Runtime, TensorRT, OpenVINO, TVM, framework exporter, or hardware kernel fails, use the runtime/exporter evidence for execution semantics and use this ONNX skill only to validate the ONNX artifact, schema, shapes, opsets, and reference expected values.
