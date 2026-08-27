# API Reference: Model I/O and Prediction

This reference covers existing Core ML artifacts. It does not cover source-framework conversion, compression, or MIL pass debugging.

## Core imports

```python
import coremltools as ct
from coremltools.models import MLModel
from coremltools.models.utils import load_spec, save_spec
```

Use `load_spec()` for inspection when prediction is not needed. It parses protobuf specs and avoids Core ML prediction. Use `MLModel` when you need metadata/feature-description convenience properties, packaging behavior, or macOS prediction.

## Artifact forms

| Form | Meaning | Editing and runtime notes |
| --- | --- | --- |
| `.mlmodel` | Single protobuf model file. | Good for many non-`mlprogram` specs. Save with `save_spec(spec, "Model.mlmodel")` or `model.save("Model.mlmodel")`. |
| `.mlpackage` | Directory package containing the model protobuf and, for `mlprogram`, external artifacts such as weights. | Required for most `mlprogram` models with weights. Save with `model.save("Model.mlpackage")` or `save_spec(spec, "Model.mlpackage", weights_dir=...)`. |
| `.mlmodelc` | Compiled Core ML runtime directory. | For prediction startup speed. It is not the right form for metadata/spec editing; keep and edit the original `.mlmodel` or `.mlpackage`. |

## `MLModel` constructor

Verified signature:

```python
MLModel(
    model,
    is_temp_package=False,
    mil_program=None,
    skip_model_load=False,
    compute_units=ct.ComputeUnit.ALL,
    weights_dir=None,
    function_name=None,
    optimization_hints=None,
)
```

Important arguments:

- `model`: path to `.mlmodel` or `.mlpackage`, or a protobuf `Model_pb2.Model` spec.
- `skip_model_load=True`: load/spec-inspect/save without compiling or loading through the Core ML framework. A model loaded this way cannot predict.
- `compute_units`: `ct.ComputeUnit.ALL`, `CPU_ONLY`, `CPU_AND_GPU`, or `CPU_AND_NE`. `CPU_AND_NE` is available only on macOS 13+.
- `weights_dir`: required when constructing an `MLModel` from an `mlprogram` spec object that has external weights.
- `function_name`: selects a non-default function in a multifunction `.mlpackage`.
- `optimization_hints`: macOS 15+ only. Supported keys include `allowLowPrecisionAccumulationOnGPU`, `reshapeFrequency`, and `specializationStrategy`.

Useful properties and methods:

```python
model = ct.models.MLModel("Model.mlpackage", skip_model_load=True)
spec = model.get_spec()          # deep copy of the protobuf spec
model.save("Edited.mlpackage")

model.author = "..."
model.license = "..."
model.short_description = "..."
model.version = "..."
model.user_defined_metadata["key"] = "value"

list(model.input_description)    # feature names
model.input_description["x"] = "input description"
model.output_description["y"] = "output description"

model.package_path               # package directory for package-backed models
model.weights_dir                # package weights directory for mlprogram models
model.compute_unit
model.function_name
```

`input_description` and `output_description` edit the short descriptions of existing features. They do not create features. To rename feature names, edit the spec with `ct.models.utils.rename_feature(...)`, then recreate and save the model.

## Spec utilities

```python
spec = load_spec("Model.mlmodel")
spec = load_spec("Model.mlpackage")

save_spec(spec, "Saved.mlmodel", auto_set_specification_version=False)
save_spec(spec, "Saved.mlpackage", weights_dir=model.weights_dir)
```

Contracts:

- `load_spec(model_path)` accepts a `.mlmodel` file or `.mlpackage` directory and returns a protobuf model spec.
- `save_spec(spec, filename, auto_set_specification_version=False, weights_dir=None)` writes `.mlmodel` or `.mlpackage` according to the filename extension.
- For an `mlprogram` package, pass `weights_dir` when saving or reconstructing from a spec object.
- If no extension is supplied to `save_spec`, `.mlmodel` is appended.

## Feature inspection

Common protobuf fields:

```python
spec.WhichOneof("Type")
spec.specificationVersion
spec.description.input
spec.description.output
spec.description.metadata
spec.description.predictedFeatureName
spec.description.predictedProbabilitiesName
spec.description.defaultFunctionName
spec.description.functions
spec.description.state
```

For each feature, inspect `feature.name`, `feature.shortDescription`, and `feature.type.WhichOneof("Type")`. Common feature kinds are `multiArrayType`, `imageType`, scalar numeric/string types, dictionaries, sequences, and states.

## Prediction contract

Python prediction uses the Core ML framework and is macOS-only. Linux can usually inspect and edit specs, but it cannot verify `predict()`, `CompiledMLModel`, compute device usage, or compute plans.

```python
model = ct.models.MLModel(
    "Model.mlpackage",
    compute_units=ct.ComputeUnit.CPU_ONLY,
)

out = model.predict({"input_name": value})
```

Inputs and outputs:

- The prediction input is a `dict[str, value]` keyed by exact Core ML input feature names.
- Batch prediction uses `list[dict[str, value]]`.
- Multi-array inputs should be NumPy arrays with the expected shape and dtype.
- Image inputs should be PIL image objects. If a model uses a multi-array to represent image data, convert the image to a NumPy array and transpose/reshape to the model's expected layout.
- Outputs are dictionaries keyed by output feature names.
- Custom neural-network layers and unsupported specification versions may block Python prediction.

Platform gates:

- General Python prediction requires the Core ML framework on macOS 10.13+.
- `.mlpackage` prediction requires macOS 12+.
- `ct.ComputeUnit.CPU_AND_NE` requires macOS 13+.
- Non-empty `optimization_hints` require macOS 15+.
- Stateful prediction requires macOS 15+.

## Compiled models

`ct.models.CompiledMLModel("Model.mlmodelc")` loads a compiled model directory for prediction. A common workflow is:

1. Load the original `.mlpackage` with `MLModel` on macOS.
2. Call `get_compiled_model_path()`.
3. Copy the returned temporary `.mlmodelc` directory to a stable location while the `MLModel` object is alive.
4. Load the stable `.mlmodelc` with `ct.models.CompiledMLModel` and call `predict()`.

Compiled models are for runtime prediction. Do not use them as the source of truth for metadata or spec edits.

## Stateful models

Stateful Core ML models are `mlprogram` models targeting macOS 15/iOS 18 or newer. Runtime use:

```python
state = model.make_state()
out1 = model.predict({"x": x1}, state=state)
out2 = model.predict({"x": x2}, state=state)
state_value = state.read_state(name="state_name")
state.write_state(name="state_name", value=new_value)
```

State is passed by reference and is not saved back into the model artifact. Batch prediction cannot use `state`; use unbatched dictionaries when passing a state object.

See [workflows.md](workflows.md) for task recipes and [troubleshooting.md](troubleshooting.md) for failures.
