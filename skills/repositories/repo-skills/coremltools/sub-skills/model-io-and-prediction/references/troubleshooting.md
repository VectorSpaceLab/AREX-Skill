# Troubleshooting: Model I/O and Prediction

Use this checklist when loading, inspecting, saving, packaging, or predicting with Core ML artifacts fails.

## Linux can inspect but not predict

Symptoms:

- `Failed to load _MLModelProxy`
- `Unable to load CoreML.framework. Cannot make predictions.`
- `predict()` works on a Mac but fails on Linux.

Action:

1. Do not treat this as a model-format failure by itself.
2. Use spec-only inspection:

   ```bash
   python scripts/inspect_mlmodel.py Model.mlpackage --json
   ```

3. For Python inspection, prefer:

   ```python
   from coremltools.models.utils import load_spec
   spec = load_spec("Model.mlmodel")
   ```

4. If `MLModel` convenience fields are needed, try `skip_model_load=True`, but still do not call `predict()`.
5. Move prediction, `CompiledMLModel`, compute-device, and compute-plan validation to a macOS runtime with Core ML available.

## `.mlpackage` parsing fails

Symptoms:

- `Unable to load libmodelpackage`
- package load errors even though the directory exists;
- missing root model inside a package.

Action:

1. Confirm the path is a directory ending in `.mlpackage`.
2. Try the bundled inspector; it attempts `load_spec()` and then a conservative fallback to the package's root model file if present.
3. If package support is unavailable, use an environment with the package library installed for repackaging or direct `.mlpackage` operations.
4. Do not manually move weights unless you know the package layout and will re-run inspection afterward.

## `mlprogram` spec object fails to load or save

Symptom:

- `MLModel of type mlProgram cannot be loaded just from the model spec object.`
- `spec of type mlProgram cannot be saved without the weights file.`

Cause: `mlprogram` weights are external to the protobuf spec.

Action:

```python
import coremltools as ct

model = ct.models.MLModel("Program.mlpackage", skip_model_load=True)
spec = model.get_spec()

edited = ct.models.MLModel(
    spec,
    weights_dir=model.weights_dir,
    skip_model_load=True,
)
edited.save("EditedProgram.mlpackage")
```

When using `save_spec`, pass `weights_dir=model.weights_dir` for `mlprogram` packages.

## Wrong extension or artifact form

Symptoms:

- save error saying an ML Program extension must be `.mlpackage`;
- output path unexpectedly becomes `.mlmodel`;
- a compiled `.mlmodelc` is being edited like a source model.

Action:

- Save package-backed `mlprogram` models as `.mlpackage`.
- Save simple protobuf specs as `.mlmodel` when no external weights are needed.
- Keep `.mlmodelc` for runtime prediction only; edit the original `.mlmodel` or `.mlpackage`.
- If `save_spec` receives a filename without an extension, it appends `.mlmodel`.

## Prediction input dictionary errors

Symptoms:

- `data parameter must be either a dict or list of dict`;
- missing input key;
- unexpected extra input key;
- wrong dtype, shape, or image object type;
- batch prediction fails with state.

Action:

1. Inspect exact names and feature types:

   ```bash
   python scripts/inspect_mlmodel.py Model.mlmodel
   ```

2. Use exact input feature names as dictionary keys.
3. For `multiArrayType`, pass a NumPy array with the expected shape.
4. For `imageType`, pass a PIL image. If the model expects a multi-array that semantically represents an image, convert the image to NumPy and transpose/reshape explicitly.
5. For batch prediction, pass `list[dict[str, value]]`.
6. Do not pass `state` with batch prediction; state is only for unbatched calls.

## Prediction unavailable on macOS

Symptoms:

- model loads but `predict()` fails;
- spec version unsupported;
- custom neural-network layer blocks prediction;
- `.mlpackage` prediction fails on an older macOS.

Action:

1. Check macOS version and artifact form.
2. General Python prediction requires macOS 10.13+.
3. `.mlpackage` prediction requires macOS 12+.
4. `CPU_AND_NE` requires macOS 13+.
5. Non-empty `optimization_hints` require macOS 15+.
6. Stateful prediction requires macOS 15+.
7. If the spec version is newer than the installed Core ML runtime supports, inspect and save with `skip_model_load=True`, then validate prediction on a newer macOS.
8. If the model contains custom layers, Python prediction may be unsupported even if loading succeeds.

## Compute-unit and optimization-hint errors

Symptoms:

- `compute_units parameter must be of type coremltools.ComputeUnit`;
- `CPU_AND_NE is only available on macOS >= 13.0`;
- `Optimization hints are only available on macOS >= 15.0`;
- unrecognized optimization hint key.

Action:

```python
import coremltools as ct

model = ct.models.MLModel(
    "Model.mlpackage",
    compute_units=ct.ComputeUnit.CPU_ONLY,
)
```

Use enum values, not strings. Only use non-empty `optimization_hints` on macOS 15+. Valid keys include `allowLowPrecisionAccumulationOnGPU`, `reshapeFrequency`, and `specializationStrategy`.

## Compiled model path disappears

Symptom: `get_compiled_model_path()` returns a path, but it is gone later.

Cause: the compiled path returned by `MLModel` is temporary and tied to the lifetime of the Python object.

Action:

```python
import shutil
compiled_path = model.get_compiled_model_path()
shutil.copytree(compiled_path, "Model.mlmodelc", dirs_exist_ok=True)
```

Copy it while the source `MLModel` object is alive. Keep the original `.mlpackage` for future edits.

## Stateful predictions are surprising

Symptoms:

- repeated predictions produce different values;
- comparison with a source framework appears nondeterministic;
- state read/write fails.

Action:

- Remember that state is mutable runtime data, not an input/output copied through the model file.
- Create separate state objects with `model.make_state()` when comparing independent sequences.
- Reset or overwrite state explicitly with `state.write_state(...)` before reproducibility checks.
- Run stateful APIs only on macOS 15+.

## When to route elsewhere

- If the artifact does not exist yet and must be converted from a source framework, route to `../convert-models/`.
- If the task is weight compression, quantization, palettization, pruning, or size/performance optimization, route to `../optimize-models/`.
- If the task is MIL graph analysis, custom passes, or pass-pipeline debugging, route to `../mil-and-debugging/`.

For routine recipes, see [workflows.md](workflows.md). For API contracts, see [api-reference.md](api-reference.md).
