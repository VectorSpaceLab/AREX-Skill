# Cross-Cutting Troubleshooting

Use this reference for import, install, native-library, optional dependency, and platform failures that can affect multiple `coremltools` workflows. For workflow-specific symptoms, continue to the relevant sub-skill troubleshooting file.

## First diagnostic

Run the root diagnostic in the same Python environment that will run conversion or inspection:

```bash
python scripts/check_coremltools_env.py
python scripts/check_coremltools_env.py --smoke
```

Interpretation:

- Import failure means the package is not installed or the current working directory shadows the package.
- Optional dependency gates marked `missing` mean the corresponding converter family or `optimize.torch` path is not available yet.
- `--smoke` failure with `BlobWriter` or `libmilstoragepython` points to ML Program package-writing native components.
- Prediction/runtime warnings on Linux are expected; do not treat them as proof the model artifact is invalid.

## `Failed to load _MLModelProxy` or Core ML runtime unavailable

Likely cause: the Python package can import, but Core ML runtime bindings are not available on the current platform. This is common on Linux.

Actions:

1. Continue with conversion, spec inspection, and saving when those operations work.
2. Avoid `MLModel.predict`, `CompiledMLModel`, compute device, and compute plan checks on Linux.
3. Use [`sub-skills/model-io-and-prediction/scripts/inspect_mlmodel.py`](../sub-skills/model-io-and-prediction/scripts/inspect_mlmodel.py) for spec-only inspection.
4. Move prediction validation to macOS or a documented remote Core ML runtime.

## `BlobWriter not loaded` or missing `libmilstoragepython`

Likely cause: the active package build lacks native components needed to save ML Program packages.

Actions:

1. Verify whether the failure is ML Program-specific:

   ```bash
   python sub-skills/mil-and-debugging/scripts/mil_smoke.py --convert-to neuralnetwork --output smoke.mlmodel
   python sub-skills/mil-and-debugging/scripts/mil_smoke.py --convert-to mlprogram --output smoke.mlpackage
   ```

2. Install a compatible wheel or build the source checkout so `libmilstoragepython` is available.
3. If the user only needs graph debugging, use `convert_to="milinternal"` or neural-network conversion while you isolate the source problem.

## Optional converter dependency missing

Symptoms include `PyTorch not found`, `TensorFlow not found`, `Sklearn not found`, disabled classic converter APIs, or `source="auto"` failing to detect a framework.

Actions:

1. Install only the dependency family required by the source model.
2. Re-run `python scripts/check_coremltools_env.py` and confirm the optional gate changed to available.
3. Run a tiny native conversion for that dependency before applying the workflow to a large model.
4. If a package imports but coremltools warns it is outside a supported version range, use the repo/documented compatibility version or narrow the workflow.

## NumPy/protobuf/version skew

Symptoms include protobuf parse errors, unexpected generated-message errors, or import-time failures after upgrading dependencies.

Actions:

1. Reproduce in a clean environment with only `coremltools` and the required optional source framework.
2. Prefer the dependency versions pulled by a compatible coremltools wheel before adding test/doc requirements.
3. Avoid mixing old TensorFlow pins with very new Python, protobuf, or NumPy unless the converter path explicitly supports that combination.

## Save/load/predict confusion

- Conversion returning `MLModel` does not mean prediction is available on the current host.
- `mlprogram` artifacts should normally be saved as `.mlpackage`; many neural-network/classic specs can be `.mlmodel`.
- Use `skip_model_load=True` when conversion should avoid runtime loading.
- Route save/load/metadata/prediction questions to [`model-io-and-prediction`](../sub-skills/model-io-and-prediction/).

## When to stop and ask for a different runtime

Stop instead of retrying blindly when:

- The task specifically requires `MLModel.predict`, compiled model latency, device-plan introspection, ModelRunner, or Neural Engine/GPU runtime behavior, and no macOS/Core ML runtime is available.
- The source framework required for conversion does not support the user's Python or platform.
- A full source build is required and the host lacks CMake/compiler/zsh/conda prerequisites or sufficient time budget.
- A converter gap is an unsupported operator/model feature rather than a missing dependency; route to [`mil-and-debugging`](../sub-skills/mil-and-debugging/) for reduction/custom-op strategy.
