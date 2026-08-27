# Deployment and project troubleshooting

Start with the safe probes:

```bash
python sub-skills/deployment-and-projects/scripts/check_deployment_dependencies.py
python sub-skills/deployment-and-projects/scripts/project_import_probe.py --repo-root <fastreid-root> --project all
```

Use `--json` when another tool needs machine-readable output, and `--strict` when missing selected dependencies/imports should produce a non-zero exit code.

## `ModuleNotFoundError: onnx` before `--help`

FastReID v1.3's ONNX export surface imports `onnx`, `onnxoptimizer`, and `onnxsim` before constructing the argument parser. Therefore a missing `onnx` package can make a help command fail before it displays usage.

Resolution:

1. Confirm with `check_deployment_dependencies.py`.
2. Install the ONNX export stack only in the user's intended export environment: `onnx`, `onnxoptimizer`, `onnxsim`, and compatible `torch`.
3. If only ONNX Runtime inference is needed, `onnxruntime` is still required separately.
4. Re-run a dependency probe before attempting export.

Do not treat this as proof that the model config or parser flags are wrong.

## `ModuleNotFoundError: onnxruntime`

ONNX export and ONNX inference use different optional packages. Export can succeed without ONNX Runtime, but inference and deployed-output comparison require `onnxruntime`.

Resolution:

- Install ONNX Runtime compatible with the target CPU/GPU runtime.
- Confirm that the model path points to a real `.onnx` artifact.
- Check that input names and input shapes are read from the session rather than hard-coded.

## `ModuleNotFoundError: tensorrt` before `--help`

The TensorRT export surface imports `tensorrt` before argument parsing. A help failure with this import error means the TensorRT Python package/runtime is not present.

Resolution:

1. Confirm `tensorrt` with `check_deployment_dependencies.py`.
2. Confirm NVIDIA GPU, driver, CUDA runtime, and TensorRT version compatibility.
3. Use TensorRT only in the target deployment environment; CPU-only environments have no faithful substitute.
4. Rebuild engines after changing TensorRT version, GPU architecture, driver/runtime, batch size, or input shape.

## Missing `caffe`, Caffe protobuf, or conversion helpers

Caffe conversion/inference is an optional external runtime path. This generated skill intentionally does not bundle generated Caffe protobuf code or vendor conversion helpers.

Resolution:

- Use a Caffe/PyCaffe environment that can import `caffe`.
- Ensure the conversion helper used by the Caffe export path is installed or vendored in the application environment.
- After conversion, inspect and edit the generated prototxt as needed: remove unsupported `ceil_mode: false`, add global average pooling when required, and expose the final blob as `output`.
- Validate Caffe features against PyTorch features on identical local images.

## Unsupported ONNX or TensorRT operators

Symptoms include ONNX export warnings, ONNX simplifier validation failure, TensorRT parser errors, missing output tensors, or large numeric drift.

Common causes:

- A project meta-architecture/head/backbone was not imported before model build.
- A config uses a layer that the exporter/runtime cannot lower directly.
- `FastGlobalAvgPool` was not replaced with `GlobalAvgPool` for ONNX export.
- TensorRT parser cannot consume an operator emitted with ATen fallback.
- Non-local blocks, custom project heads, or distillation-only paths were left enabled for deployment.

Triage:

1. Start from a standard baseline model and verify export.
2. Import the project package and apply its config hook before merge/build.
3. Disable pretraining downloads and load only the intended checkpoint.
4. Compare PyTorch vs deployed outputs before switching to FP16 or INT8.
5. If TensorRT parsing fails, inspect every parser error and simplify the ONNX graph only when simplification validates.

## Shape, batch, and feature-size mismatch

FastReID deployment surfaces derive image height/width from `cfg.INPUT.SIZE_TEST` or explicit `--height/--width` arguments. TensorRT engines also bake or constrain batch/binding shapes.

Resolution:

- Match `INPUT.SIZE_TEST`, export `--batch-size`, runtime `--batch-size`, and TensorRT binding shapes.
- For ONNX, verify whether the graph was exported for a fixed batch or supports dynamic axes in the user's export implementation.
- For TensorRT, rebuild the engine when max batch or input shape changes.
- For FastRT C++, update `MAX_BATCH_SIZE`, `INPUT_H`, `INPUT_W`, and `OUTPUT_SIZE` constants to match the trained model.
- If comparison fails only on the final partial batch, check zero-padding and trimming logic.

## Device or engine mismatch

Symptoms include CUDA context failures, engine deserialization failure, illegal memory access, no compatible GPU, or TensorRT version errors.

Resolution:

- Build and deserialize TensorRT engines on compatible driver/runtime/GPU targets.
- Match `cfg.MODEL.DEVICE` to the environment used for export/inference.
- Do not load a GPU-only engine in CPU-only environments.
- Rebuild after changing GPU architecture, TensorRT major/minor version, CUDA driver/runtime, precision mode, or batch/shape.

## Preprocessing mismatch

Large output differences often come from preprocessing rather than export corruption.

Checklist:

- Read images with OpenCV-style BGR and convert to RGB if following FastReID's deployment path.
- Resize to the same `(width, height)` used during export/runtime.
- Use `float32` CHW tensors with a batch dimension.
- Apply the same normalization expected by the backend. The Caffe inference path applies ImageNet mean/std normalization in pixel units; the ONNX/TensorRT examples use RGB CHW `float32` and normalize features after inference.
- L2-normalize features before equality checks when comparing deployment surfaces.

## Project import path failures

Symptoms include `ModuleNotFoundError: fastattr`, `fastface`, `fastretri`, `partialreid`, `naic`, `autotuner`, or `fastdistill`.

Resolution:

1. Pass an explicit application checkout root to `project_import_probe.py`.
2. Ensure both the FastReID root and the selected project directory are on `sys.path` or installed equivalently.
3. Import the project package before merging configs or building models/datasets.
4. For project-only dependencies, install only what the selected project requires.

Known project-specific import hazards:

- `FastAttr` package import can require `mat4py` for Market1501/Duke attribute annotation modules.
- `FastClas` package-wide import may fail if a referenced `distracted_driver` module is absent. Import-probe the package before using it, or use a repaired package initializer in the user's application environment.
- `FastFace` package import requires `bcolz` for verification dataset registration; `mxnet` is optional for `.rec` train data.
- `FastTune` import requires Ray Tune dependencies and should be treated as a long-running tuning stack, not as a quick smoke test.
- `FastRT` is C++/TensorRT, not a regular Python import package.

## Project config injection failures

Symptoms include YACS errors such as unknown config key, registry `KeyError`, or model builder failure after merging a project config.

Resolution by project:

- `FastAttr`: call `add_attr_config(cfg)` before merging configs that use BCE attribute-loss keys or `TEST.THRES`.
- `FastFace`: call `add_face_cfg(cfg)` before merging configs that use `DATASETS.REC_PATH`, `MODEL.BACKBONE.DROPOUT`, or `MODEL.HEADS.PFC`.
- `FastRetri`: call `add_retri_config(cfg)` before merging configs that use `TEST.RECALLS`.
- `PartialReID`: call `add_partialreid_config(cfg)` before merging configs that use `TEST.DSR`.
- `NAIC20`: call `add_naic_config(cfg)` before merging configs that use `DATASETS.RM_LT` or `TEST.SAVE_DISTMAT`.
- `FastDistill`: import `fastdistill` before selecting distillation-specific meta-architectures/backbones; teacher configs and weights must be local.

If the failure is about where dataset files live or how a dataset class parses labels, route to `../data-and-datasets/`. If the failure is about tensor shapes or model feature outputs, route to `../modeling-and-inference/`. If the failure is about train/eval launch flags, route to `../training-and-evaluation/`.

## Generated Caffe protobuf is not bundled

If a Caffe workflow asks for generated protobuf code that is not present, do not copy generated/vendor files into this runtime skill. Use a properly prepared Caffe environment and conversion helper stack in the user's application workspace. Record Caffe as optional/unverified until that environment can import `caffe`, convert a model, run inference, and compare against PyTorch.
