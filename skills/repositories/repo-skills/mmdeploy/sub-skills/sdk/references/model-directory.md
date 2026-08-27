# SDK Model Directory

An MMDeploy SDK model directory is the runtime package produced by conversion
when SDK metadata is dumped. It is the unit consumed by `mmdeploy_runtime`, C/C++
SDK wrappers, Java wrappers, and C# wrappers.

## Expected Layout

A typical TensorRT directory looks like this:

```text
sdk_model_dir/
├── deploy.json
├── detail.json
├── pipeline.json
├── end2end.onnx
├── end2end.engine
├── output_pytorch.jpg        # optional conversion visualization
└── output_tensorrt.jpg       # optional conversion visualization
```

Other backends use different artifacts, but the SDK JSON files remain the
important handoff. The directory, not one individual artifact, is the `model_path`
for SDK inference.

## `deploy.json`

`deploy.json` is the SDK deployment manifest. It declares:

- MMDeploy version.
- SDK task class name, such as `Classifier`, `Detector`, `Segmentor`,
  `Restorer`, `TextDetector`, `TextRecognizer`, `PoseDetector`,
  `RotatedDetector`, or `VideoRecognizer`.
- `models`: one or more backend model entries with fields such as:
  - `name`: logical model name.
  - `net`: main backend network file.
  - `weights`: companion weights file when the backend separates graph and
    weights.
  - `backend`: backend name such as `tensorrt`, `onnxruntime`, `ncnn`,
    `openvino`, `snpe`, `rknn`, `ascend`, `coreml`, `torchscript`, `tvm`, or
    another supported backend.
  - `precision`, `batch_size`, and `dynamic_shape`.
- `customs`: extra files required by some tasks, such as OCR dictionaries.

Use `deploy.json` to decide the runtime task class and to check that all named
model artifacts are present.

## `pipeline.json`

`pipeline.json` is the runtime execution graph. It usually contains:

- `pipeline.input` and `pipeline.output` names.
- A preprocess task, often a `Transform` task with serialized image transforms.
- An inference task, often `module: Net`, with `input_map` and optional
  `output_map`.
- A postprocess task tied to the originating codebase/task.
- Optional flags such as dynamic batching or backend-specific properties.

SDK runtime APIs need this file to reproduce the preprocessing and
postprocessing that the backend engine alone does not contain. A backend engine
file without `pipeline.json` is a converter artifact, not an SDK model package.

## `detail.json`

`detail.json` is provenance and configuration detail. It can include:

- MMDeploy version.
- Source codebase name and version.
- Original model config and checkpoint identity.
- Codebase, ONNX/IR, backend, and calibration configuration sections.

Treat this file as a diagnostic aid. It can contain paths or names from the
conversion environment, so portable SDK use should depend on files packaged in
the SDK model directory rather than on the original conversion workspace.

## Backend / IR Artifacts

Common artifact families:

| Backend or IR | Typical files | SDK note |
| --- | --- | --- |
| ONNXRuntime | `.onnx` | Often CPU or CUDA capable depending on runtime package. |
| TensorRT | `.engine` plus often `.onnx` | Engine is hardware/version sensitive; SDK still needs JSON files. |
| OpenVINO | `.xml` + `.bin` | Both graph and weights must be present. |
| NCNN | `.param` + `.bin` | Both graph and weights must be present. |
| SNPE | `.dlc` | Device/runtime constraints are strict; see troubleshooting. |
| RKNN | `.rknn` | Target-device/toolkit specific. |
| Ascend | `.om` | Accelerator/toolkit specific. |
| CoreML | `.mlpackage` | Platform/runtime specific. |
| TVM | library plus metadata text/code files | Artifact names can vary by TVM build mode. |
| TorchScript | `.pt` or saved TorchScript file | CPU/GPU support follows LibTorch/runtime build. |

The exact names are whatever `deploy.json` records. Do not infer the expected
file name only from the backend type.

## Directory Versus Engine-File Rule

Use this decision table when a user provides a path:

| User path | Correct route |
| --- | --- |
| Directory containing `deploy.json` and `pipeline.json` | Valid SDK `model_path`; continue SDK inference checks. |
| `.zip` containing a complete SDK model package | Valid only if the SDK was built with zip-model support. |
| Single `.engine`, `.onnx`, `.xml`, `.param`, `.dlc`, `.rknn`, `.om`, or `.pt` | Not an SDK model package; use converter/backend APIs or regenerate with SDK metadata. |
| Directory with backend files but missing JSON metadata | Not enough for SDK runtime; regenerate with `--dump-info`. |
| Directory with JSON metadata but missing files named by `deploy.json` | Broken package; copy the missing artifacts or rerun conversion. |

## Zip Model Note

SDK can read a model directory directly. It can also read a zip archive or model
bytes only when the SDK build enables zip-model support (`MMDEPLOY_ZIP_MODEL`).
If a zip model fails to load:

1. Confirm the zip contains the same files that would appear in the directory.
2. Confirm the runtime SDK was built with zip-model support.
3. If the zip is encrypted, decrypt to bytes before calling the memory-loading
   API.
4. Fall back to the plain directory format when build flags are unknown.

## Validation Checklist

Run these checks before diagnosing language bindings:

```bash
test -f sdk_model_dir/deploy.json
test -f sdk_model_dir/pipeline.json
test -f sdk_model_dir/detail.json
python -m json.tool sdk_model_dir/deploy.json >/dev/null
python -m json.tool sdk_model_dir/pipeline.json >/dev/null
```

Optional artifact check:

```python
import json
from pathlib import Path

root = Path('sdk_model_dir')
deploy = json.loads((root / 'deploy.json').read_text())
missing = []
for model in deploy.get('models', []):
    for key in ('net', 'weights'):
        value = model.get(key)
        if value and not (root / value).exists():
            missing.append(value)
for value in deploy.get('customs', []):
    if value and not (root / value).exists():
        missing.append(value)
print('missing:', missing)
print('task:', deploy.get('task'))
```

Stop on any missing required file. Do not attempt to fix SDK runtime code while
the package itself is incomplete.
