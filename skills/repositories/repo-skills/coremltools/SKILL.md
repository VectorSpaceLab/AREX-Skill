---
name: coremltools
description: "Operate Core ML Tools workflows for model conversion, Core ML
  artifact I/O, optimization, MIL debugging, and platform-aware
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Core ML Tools

Use this repo skill when a task involves the `coremltools` Python package, Core ML model conversion, `.mlmodel`/`.mlpackage` artifacts, Core ML optimization/compression, MIL graph debugging, or macOS-vs-Linux Core ML runtime constraints.

## Start here

1. Confirm the package imports in the active environment:

   ```bash
   python scripts/check_coremltools_env.py
   ```

   Add `--smoke` only when you want a tiny MIL-to-MLProgram conversion/save check without prediction.
2. Identify the task family from the route map below.
3. Check [capability map](references/capability-map.md) for dependency/platform gates before promising that a workflow is verified.
4. Use [troubleshooting](references/troubleshooting.md) for install/import/native-library/platform failures that affect multiple workflows.
5. Use [repo provenance](references/repo-provenance.md) before deciding whether this skill is stale for a newer checkout.

## Route map

| User task | Read |
| --- | --- |
| Convert PyTorch, TensorFlow, MIL, scikit-learn, XGBoost, LightGBM, or LibSVM models to Core ML | [`sub-skills/convert-models/`](sub-skills/convert-models/) |
| Choose `ct.convert` inputs/outputs, deployment targets, `mlprogram` vs `neuralnetwork`, precision, pass pipelines, or optional framework dependencies | [`sub-skills/convert-models/`](sub-skills/convert-models/) |
| Load, save, inspect, edit, or package existing `.mlmodel`/`.mlpackage` artifacts | [`sub-skills/model-io-and-prediction/`](sub-skills/model-io-and-prediction/) |
| Use `MLModel.predict`, compiled models, compute units/devices/plans, stateful prediction, image/multiarray prediction inputs, or macOS runtime checks | [`sub-skills/model-io-and-prediction/`](sub-skills/model-io-and-prediction/) |
| Quantize, palettize, prune, decompress, or inspect compression metadata for Core ML packages | [`sub-skills/optimize-models/`](sub-skills/optimize-models/) |
| Use optional `coremltools.optimize.torch` workflows with calibration data, fine-tuning, QAT, or Torch-side compression before export | [`sub-skills/optimize-models/`](sub-skills/optimize-models/) |
| Build/inspect MIL programs, control pass pipelines, register custom/composite ops, diagnose typed execution, or use experimental debug/perf utilities | [`sub-skills/mil-and-debugging/`](sub-skills/mil-and-debugging/) |
| Understand package installation, optional dependencies, source-build scripts, or test-script boundaries | [`references/install-and-build.md`](references/install-and-build.md) |

## Dependency and platform rules

- Base `coremltools` import is not enough to verify every converter. PyTorch, TensorFlow, scikit-learn, XGBoost, LightGBM, and LibSVM routes are optional dependency-gated.
- Linux can convert and inspect many artifacts, but `MLModel.predict`, `CompiledMLModel`, compute-device/compute-plan APIs, and ModelRunner workflows generally require macOS Core ML runtime support.
- `mlprogram` artifacts usually save as `.mlpackage`; many older/classic neural-network specs can save as `.mlmodel`.
- Use `skip_model_load=True` when conversion should avoid runtime loading on the current host.
- Source checkouts can lack native runtime libraries included in wheels. If ML Program save fails with `BlobWriter`/`libmilstoragepython`, read [install-and-build](references/install-and-build.md).

## Bundled helpers

- [`scripts/check_coremltools_env.py`](scripts/check_coremltools_env.py): package import, optional dependency gates, and optional tiny conversion smoke.
- [`sub-skills/convert-models/scripts/convert_torch_toy.py`](sub-skills/convert-models/scripts/convert_torch_toy.py): tiny PyTorch-to-Core ML conversion smoke when PyTorch is installed.
- [`sub-skills/model-io-and-prediction/scripts/inspect_mlmodel.py`](sub-skills/model-io-and-prediction/scripts/inspect_mlmodel.py): spec-only inspection of `.mlmodel` or `.mlpackage` artifacts.
- [`sub-skills/optimize-models/scripts/optimize_coreml_smoke.py`](sub-skills/optimize-models/scripts/optimize_coreml_smoke.py): tiny Core ML optimization smoke.
- [`sub-skills/mil-and-debugging/scripts/mil_smoke.py`](sub-skills/mil-and-debugging/scripts/mil_smoke.py): MIL Builder conversion/save smoke for `mlprogram` or `neuralnetwork`.

## Safe operating stance

- Do not run long training, downloads, full test suites, or prediction checks unless the user explicitly requests them and the required framework/platform is present.
- Prefer tiny conversion/spec/optimization smokes before applying guidance to large models.
- Preserve original source-model semantics when debugging conversion; shrink to a reproducer before introducing custom ops or pass-pipeline changes.
- Keep package-operation tasks separate from repository-maintenance tasks. Use maintainer scripts only when the user is working in the repository checkout and wants source build/test behavior.
