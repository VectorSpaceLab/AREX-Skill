# Core ML Tools Capability Map

Use this reference to choose the right `coremltools` sub-skill and to understand which dependencies or platforms must be available before claiming a workflow is verified.

## Primary workflows

| Workflow | Route | Inputs | Outputs | Dependency/platform gates |
| --- | --- | --- | --- | --- |
| Convert source models to Core ML | [`sub-skills/convert-models/`](../sub-skills/convert-models/) | PyTorch TorchScript or `ExportedProgram`, TensorFlow graph/Keras/SavedModel, MIL `Program`, scikit-learn/XGBoost/LightGBM/LibSVM models | `MLModel`, `.mlmodel`, `.mlpackage`, or MIL `Program` | Source framework must import; PyTorch/TensorFlow/classic converters are optional dependency-gated. |
| Inspect, edit, save, package, and predict with Core ML artifacts | [`sub-skills/model-io-and-prediction/`](../sub-skills/model-io-and-prediction/) | `.mlmodel`, `.mlpackage`, protobuf spec, `MLModel` | metadata/spec summaries, edited/saved artifacts, prediction results when runtime is available | Spec inspection is cross-platform; `predict`, compiled models, device plans, and runtime states generally require macOS Core ML. |
| Compress and optimize models | [`sub-skills/optimize-models/`](../sub-skills/optimize-models/) | `mlprogram` `MLModel` packages or PyTorch models | quantized/palettized/pruned/decompressed artifacts | `coremltools.optimize.coreml` is package-gated; `coremltools.optimize.torch` additionally requires compatible PyTorch and data/training loop for calibration/fine-tuning. |
| Advanced MIL and conversion debugging | [`sub-skills/mil-and-debugging/`](../sub-skills/mil-and-debugging/) | MIL Builder programs, converter failures, pass pipelines, custom op specs, debug inputs | reduced reproducer, pass-pipeline settings, custom op routes, precision/debugger plan | Experimental runtime debug utilities may need macOS prediction or remote-device support. |

## Support workflows

| Support task | Runtime location | Notes |
| --- | --- | --- |
| Check package import and optional dependency gates | [`scripts/check_coremltools_env.py`](../scripts/check_coremltools_env.py) | Safe by default; add `--smoke` to try a tiny MIL-to-MLProgram conversion without prediction. |
| Understand install/build/test scripts | [`references/install-and-build.md`](install-and-build.md) | Source build/test scripts are maintainer-oriented and intentionally not bundled as runtime commands. |
| Diagnose cross-cutting import/platform failures | [`references/troubleshooting.md`](troubleshooting.md) | Workflow-specific failures live in each sub-skill's troubleshooting reference. |
| Check staleness | [`references/repo-provenance.md`](repo-provenance.md) | Refresh if commit/version/signatures differ. |

## Optional dependency map

| Optional dependency | Enables | Common constraint |
| --- | --- | --- |
| `torch` | PyTorch conversion, `torch.export`, `coremltools.optimize.torch`, Torch comparators | Core ML Tools warns about untested/newer versions; optimize.torch requires a minimum torch version. CPU is enough for many conversion smokes. |
| `tensorflow` | TensorFlow 1/2 conversion | Version and Python compatibility are strict, especially for TensorFlow 1.x and older TensorFlow 2.x variants. |
| `scikit-learn` | sklearn classic converters | Core ML Tools may disable APIs outside tested sklearn version ranges. |
| `xgboost`, `lightgbm`, `libsvm` | classic tree/SVM converters | Install only for the converter family being used; they are not needed for PyTorch/TensorFlow conversion. |
| `Pillow` | Image prediction inputs and some image workflows | Prediction still needs Core ML runtime; PIL only prepares image values. |
| macOS Core ML runtime | `MLModel.predict`, `CompiledMLModel`, compute devices/plans, ModelRunner | Linux can inspect and save many artifacts but should not promise prediction. |

## Verification status from construction

- Verified during construction: package import, public signature inspection, `coremltools.optimize.coreml` import, MIL-to-MLProgram conversion/save using a matching 9.1.dev1 runtime wheel, and help/syntax checks for bundled scripts.
- Not verified during construction: macOS prediction/runtime/device APIs, ModelRunner, TensorFlow conversion, PyTorch conversion, `coremltools.optimize.torch`, and every classic converter variant.
- Generated guidance preserves those unverified surfaces as optional/dependency-gated instead of presenting them as guaranteed.
