# Workflows: Model I/O and Prediction

Use these workflows for existing Core ML artifacts. For conversion from PyTorch, TensorFlow, scikit-learn, ONNX, or other source models, route to `../convert-models/`. For compression, route to `../optimize-models/`. For MIL debugging and custom passes, route to `../mil-and-debugging/`.

## 1. Inspect an artifact without prediction

Use the bundled inspector first when you only need model type, specification version, inputs, outputs, states, functions, and metadata.

```bash
python scripts/inspect_mlmodel.py Model.mlmodel
python scripts/inspect_mlmodel.py Model.mlpackage --json
```

The script uses `coremltools.models.utils.load_spec` and does not call `MLModel.predict()`, so it is suitable for Linux spec inspection when coremltools can parse the artifact.

Minimal Python equivalent:

```python
from coremltools.models.utils import load_spec

spec = load_spec("Model.mlmodel")
print(spec.WhichOneof("Type"))
print(spec.specificationVersion)
print(spec.description.input)
print(spec.description.output)
print(spec.description.metadata)
```

## 2. Load with `MLModel` for metadata and feature descriptions

Use `skip_model_load=True` if you need `MLModel` convenience properties but do not need prediction.

```python
import coremltools as ct

model = ct.models.MLModel("Model.mlmodel", skip_model_load=True)
print(list(model.input_description))
print(list(model.output_description))
print(model.get_spec().WhichOneof("Type"))
```

For package-backed `mlprogram` models:

```python
model = ct.models.MLModel("Model.mlpackage", skip_model_load=True)
print(model.package_path)
print(model.weights_dir)
```

Do not expect this object to predict if it was loaded with `skip_model_load=True` or if the environment lacks the macOS Core ML framework.

## 3. Edit metadata and feature descriptions

```python
import coremltools as ct

model = ct.models.MLModel("Model.mlmodel", skip_model_load=True)
model.author = "Team or author"
model.license = "License string"
model.short_description = "Short Xcode-facing model description"
model.version = "1.0"
model.user_defined_metadata["com.example.source"] = "training-run-123"

model.input_description["input"] = "Input tensor description"
model.output_description["output"] = "Output tensor description"
model.save("Model_with_metadata.mlmodel")
```

For an `.mlpackage`, preserve package form:

```python
model = ct.models.MLModel("Model.mlpackage", skip_model_load=True)
model.short_description = "Updated description"
model.save("Model_with_metadata.mlpackage")
```

## 4. Rename feature names in the spec

Use `rename_feature` when the actual feature name, not only the description, must change.

```python
import coremltools as ct
from coremltools.models.utils import rename_feature

model = ct.models.MLModel("Model.mlmodel", skip_model_load=True)
spec = model.get_spec()
rename_feature(spec, "old_input", "new_input", rename_inputs=True, rename_outputs=False)
rename_feature(spec, "old_output", "new_output", rename_inputs=False, rename_outputs=True)

renamed = ct.models.MLModel(spec, skip_model_load=True)
renamed.save("Renamed.mlmodel")
```

For `mlprogram` packages with external weights, pass `weights_dir` when rebuilding from a spec:

```python
model = ct.models.MLModel("Program.mlpackage", skip_model_load=True)
spec = model.get_spec()
rename_feature(spec, "old_input", "new_input")

renamed = ct.models.MLModel(
    spec,
    weights_dir=model.weights_dir,
    skip_model_load=True,
)
renamed.save("Renamed.mlpackage")
```

After a rename, inspect the saved artifact and verify downstream prediction code uses the new dictionary keys.

## 5. Save a spec directly

```python
from coremltools.models.utils import load_spec, save_spec

spec = load_spec("Model.mlmodel")
save_spec(spec, "Saved.mlmodel")
```

For `mlprogram` packages, include weights:

```python
import coremltools as ct
from coremltools.models.utils import save_spec

model = ct.models.MLModel("Program.mlpackage", skip_model_load=True)
spec = model.get_spec()
save_spec(spec, "SavedProgram.mlpackage", weights_dir=model.weights_dir)
```

If saving fails because package support is unavailable, keep the original package intact and move the edit to an environment with the package library available.

## 6. Predict with multi-array inputs on macOS

```python
import coremltools as ct
import numpy as np

model = ct.models.MLModel(
    "Model.mlmodel",
    compute_units=ct.ComputeUnit.CPU_ONLY,
)

spec = model.get_spec()
print(spec.description.input)

x = np.zeros((1, 3, 224, 224), dtype=np.float32)
out = model.predict({"input": x})
print(out.keys())
```

Rules:

- Use exact Core ML feature names as dictionary keys.
- Match the shape shown in the model description.
- Use `np.ndarray` for multi-array features.
- Use `list[dict]` for batch prediction when the model is stateless.

## 7. Predict with image inputs on macOS

For true Core ML image input features, pass a PIL image:

```python
import coremltools as ct
from PIL import Image

model = ct.models.MLModel("ImageModel.mlmodel")
img = Image.open("image.jpg").resize((224, 224))
out = model.predict({"image": img})
```

For a multi-array input that represents image data, convert to NumPy and arrange the layout expected by the model:

```python
import numpy as np
from PIL import Image

img = Image.open("image.jpg").resize((224, 224))
arr = np.asarray(img).astype(np.float32)      # H, W, C
arr = np.transpose(arr, (2, 0, 1))            # C, H, W
arr = np.reshape(arr, (1, 3, 224, 224))       # optional batch dimension
out = model.predict({"input": arr})
```

Use the spec description rather than guessing layout.

## 8. Select compute units and optimization hints

```python
import coremltools as ct

model = ct.models.MLModel(
    "Model.mlpackage",
    compute_units=ct.ComputeUnit.CPU_ONLY,
)
```

Available compute-unit choices are `ALL`, `CPU_ONLY`, `CPU_AND_GPU`, and `CPU_AND_NE`. `CPU_AND_NE` requires macOS 13+.

Optimization hints are macOS 15+ only:

```python
model = ct.models.MLModel(
    "Model.mlpackage",
    optimization_hints={
        "specializationStrategy": ct.SpecializationStrategy.FastPrediction,
    },
)
```

Use hints only when the runtime platform supports them and you accept trade-offs between prediction latency, specialization time, memory, and disk use.

## 9. Use a compiled model for repeated prediction

On macOS, a large package may take time to compile and specialize. Persist a compiled model directory only after loading the source artifact.

```python
import shutil
import coremltools as ct

model = ct.models.MLModel("LargeModel.mlpackage")
compiled_path = model.get_compiled_model_path()
shutil.copytree(compiled_path, "LargeModel.mlmodelc", dirs_exist_ok=True)

compiled = ct.models.CompiledMLModel("LargeModel.mlmodelc")
out = compiled.predict({"input": value})
```

Keep the original `.mlpackage` for edits and repackaging. Treat `.mlmodelc` as a runtime cache artifact.

## 10. Use stateful prediction at a high level

Stateful prediction requires a stateful `mlprogram` model and macOS 15+.

```python
state = model.make_state()
y1 = model.predict({"x": x1}, state=state)
y2 = model.predict({"x": x2}, state=state)

current = state.read_state(name="accumulator")
state.write_state(name="accumulator", value=current)
```

State is separate from the model file and is not saved by `model.save(...)`. Do not pass `state` with batch prediction; use one dictionary per stateful call.

## 11. Decide whether this sub-skill is the right route

Stay here for:

- loading and saving existing `.mlmodel` or `.mlpackage` artifacts;
- metadata edits;
- input/output descriptions and feature-name inspection;
- prediction dictionary construction;
- macOS prediction/platform triage;
- packaging and compiled-model runtime handling.

Route away for:

- source-framework conversion: `../convert-models/`;
- pruning, palettization, quantization, or weight compression: `../optimize-models/`;
- MIL graph internals, pass pipelines, debugging utilities, or custom passes: `../mil-and-debugging/`.

If a workflow fails, use [troubleshooting.md](troubleshooting.md).
