# Conversion Workflows

Use these recipes to choose the smallest correct converter path. All snippets assume the relevant optional source framework is already installed and compatible.

## Unified conversion checklist

1. **Choose source family.** PyTorch, TensorFlow, and MIL use `ct.convert`; scikit-learn, XGBoost, LightGBM, and LibSVM use classic converter namespaces.
2. **Load and sanity-check the source model.** Put neural-network models in inference/eval mode and run a tiny source-framework prediction if possible.
3. **Select input/output typing.** For PyTorch TorchScript, always provide `inputs` with explicit shapes. For TensorFlow, names must match graph tensors. Use `ImageType` only when the Core ML public interface should be image-based.
4. **Select Core ML format.** Prefer `mlprogram` for modern targets; use `neuralnetwork` for older OS targets.
5. **Set precision and compute load behavior.** `compute_precision` is ML-program-only. Use `skip_model_load=True` when conversion should not attempt runtime loading on the current host.
6. **Convert, inspect, then save/predict elsewhere.** This sub-skill stops after conversion and conversion-time validation. Save/load/predict routing belongs to [model-io-and-prediction](../../model-io-and-prediction/).

## PyTorch TorchScript workflow

Best for stable PyTorch conversion.

```python
import numpy as np
import torch
import coremltools as ct

class TinyNet(torch.nn.Module):
    def forward(self, x):
        return torch.relu(x * 2.0 + 1.0)

model = TinyNet().eval()
example = torch.rand(1, 3, 8, 8)
traced = torch.jit.trace(model, example)

mlmodel = ct.convert(
    traced,
    source="pytorch",
    inputs=[ct.TensorType(name="image_tensor", shape=tuple(example.shape), dtype=np.float32)],
    outputs=[ct.TensorType(name="scores")],
    minimum_deployment_target=ct.target.iOS15,
    convert_to="mlprogram",
    compute_precision=ct.precision.FLOAT32,
    compute_units=ct.ComputeUnit.CPU_ONLY,
    skip_model_load=True,
)
```

Notes:

- Call `.eval()` before tracing so dropout, batch norm, and other training-time behavior are disabled.
- If the model has data-dependent control flow, a trace may not generalize. Try `torch.jit.script` only when the model is supported, or evaluate the `torch.export` path.
- If you use image inputs, replace `TensorType` with `ImageType`, set the shape in the source tensor layout, and set `channel_first` explicitly when needed.

## PyTorch `ExportedProgram` workflow

Use when adopting PyTorch 2 export flows and the installed PyTorch version exposes the required export API.

```python
import torch
import coremltools as ct

model = torch.nn.Sequential(torch.nn.Linear(4, 3), torch.nn.ReLU()).eval()
example_inputs = (torch.rand(2, 4),)
exported = torch.export.export(model, example_inputs)

mlmodel = ct.convert(
    exported,
    source="pytorch",
    minimum_deployment_target=ct.target.iOS15,
    convert_to="mlprogram",
    skip_model_load=True,
)
```

Notes:

- `inputs` is inferred from `ExportedProgram` for ordinary tensor typing.
- Provide `inputs` only when you need `ImageType`, `EnumeratedShapes`, custom names, or custom dtypes.
- Dynamic shapes are first expressed in `torch.export`; `ct.convert` maps them to Core ML flexible shapes where supported.

## TensorFlow 2 / Keras workflow

```python
import numpy as np
import tensorflow as tf
import coremltools as ct

inputs = tf.keras.Input(shape=(28, 28, 1), name="image")
x = tf.keras.layers.Flatten()(inputs)
x = tf.keras.layers.Dense(10, activation="softmax", name="probabilities")(x)
tf_model = tf.keras.Model(inputs, x)

# Optional source sanity check.
_ = tf_model.predict(np.zeros((1, 28, 28, 1), dtype=np.float32), verbose=0)

classifier_config = ct.ClassifierConfig(
    class_labels=[str(i) for i in range(10)],
    predicted_feature_name="digit",
    predicted_probabilities_output="probabilities",
)

mlmodel = ct.convert(
    tf_model,
    source="tensorflow",
    inputs=[ct.ImageType(name="image", shape=(1, 28, 28, 1), color_layout=ct.colorlayout.GRAYSCALE)],
    classifier_config=classifier_config,
    minimum_deployment_target=ct.target.iOS15,
    convert_to="mlprogram",
    skip_model_load=True,
)
```

Notes:

- TensorFlow input/output names are graph names. Do not invent names that are absent from the graph.
- Supported artifacts include Keras models, HDF5 files, SavedModel directories, concrete functions, and graph forms supported by the installed TensorFlow frontend.
- If you only need a tensor input, omit `ImageType` and use either inferred TensorFlow placeholders or explicit `TensorType`.

## TensorFlow concrete function workflow

```python
import tensorflow as tf
import coremltools as ct

@tf.function(input_signature=[tf.TensorSpec(shape=(1, 4), dtype=tf.float32, name="x")])
def f(x):
    return {"y": tf.nn.relu(x)}

concrete = f.get_concrete_function()
mlmodel = ct.convert(
    [concrete],
    source="tensorflow",
    convert_to="mlprogram",
    minimum_deployment_target=ct.target.iOS15,
    skip_model_load=True,
)
```

Use concrete functions when the Keras object itself is not the most stable export surface.

## MIL source workflow

Use `ct.convert(program, source="milinternal", ...)` only after a MIL `Program` already exists.

```python
import coremltools as ct

mlmodel = ct.convert(
    mil_program,
    source="milinternal",
    convert_to="mlprogram",
    minimum_deployment_target=ct.target.iOS15,
    skip_model_load=True,
)
```

Build, inspect, and debug the MIL graph via [mil-and-debugging](../../mil-and-debugging/), then return here only for final conversion arguments.

## Deployment target and format decision matrix

| Deployment need | Use | Avoid |
| --- | --- | --- |
| Current Apple platforms and future-facing features | `convert_to="mlprogram"`, target iOS15/macOS12 or newer | Saving as `.mlmodel`; `neuralnetwork` target with iOS15+ |
| Older OS support | `convert_to="neuralnetwork"` or target iOS14/macOS11 or older | `compute_precision`; ML-program-only features |
| Stateful PyTorch model | `states=[ct.StateType(...)]`, target iOS18 or newer | TensorFlow state descriptors; `StateType` inside `inputs` |
| Float32 numerical fidelity | `compute_precision=ct.precision.FLOAT32` with `mlprogram` | `compute_precision` with `neuralnetwork` |
| Conversion on unsupported host runtime | `skip_model_load=True` | Assuming `predict()` works on Linux or unsupported macOS |

## Classifier conversion pattern

Use `ClassifierConfig` only when the source output is class probabilities/logits that should become a Core ML classifier interface.

```python
labels = ["cat", "dog"]
classifier_config = ct.ClassifierConfig(
    class_labels=labels,
    predicted_feature_name="label",
    predicted_probabilities_output="probabilities",
)
mlmodel = ct.convert(
    source_model,
    inputs=[ct.TensorType(name="features", shape=(1, 128))],
    classifier_config=classifier_config,
    convert_to="mlprogram",
    minimum_deployment_target=ct.target.iOS15,
)
```

If output probabilities are not named, inspect the source graph first or let the converter use the last output.

## Pass pipeline patterns

### Disable one default pass

```python
pipeline = ct.PassPipeline()
pipeline.remove_passes({"common::fuse_conv_batchnorm"})
mlmodel = ct.convert(source_model, pass_pipeline=pipeline)
```

### Skip very large constants during constant elimination

```python
pipeline = ct.PassPipeline()
pipeline.set_options("common::const_elimination", {"skip_const_by_size": "1e6"})
mlmodel = ct.convert(source_model, pass_pipeline=pipeline)
```

### Conversion-time compression-aware pipelines

```python
sparse_mlmodel = ct.convert(source_model, pass_pipeline=ct.PassPipeline.DEFAULT_PRUNING)
palettized_mlmodel = ct.convert(source_model, pass_pipeline=ct.PassPipeline.DEFAULT_PALETTIZATION)
```

For post-conversion compression workflows, route to [optimize-models](../../optimize-models/).

## Classic scikit-learn workflow

```python
from sklearn.linear_model import LinearRegression
import coremltools as ct

model = LinearRegression().fit(X_train, y_train)
mlmodel = ct.converters.sklearn.convert(
    model,
    input_features=["bedroom", "bath", "size"],
    output_feature_names="price",
)
```

Notes:

- This path is dependency- and version-gated by scikit-learn support in coremltools.
- `input_features` describes feature names and structure, not tensor shapes.
- Pipelines are supported when every step is a supported scikit-learn transformer/estimator.

## Classic XGBoost workflow

```python
import coremltools as ct

mlmodel = ct.converters.xgboost.convert(
    booster,
    feature_names=["f0", "f1", "f2"],
    target="score",
    mode="regressor",
)
```

For classifiers, set `mode="classifier"` and pass `class_labels`/`n_classes` when they cannot be inferred safely.

## Classic LightGBM workflow

```python
import coremltools as ct

mlmodel = ct.converters.lightgbm.convert(
    lgbm_model,
    feature_names=["age", "income", "region_one_hot"],
    target="classProbability",
    mode="classifier",
    class_labels=["no", "yes"],
)
```

One-hot encode categorical features before training; LightGBM categorical `"=="` splits are not supported by this converter.

## Classic LibSVM workflow

```python
import coremltools as ct

mlmodel = ct.converters.libsvm.convert(
    libsvm_model,
    input_names=["x0", "x1"],
    target_name="target",
    probability="classProbability",
)
```

Use `input_names="features"` and `input_length=N` for one array-valued input.

## Bundled PyTorch toy conversion script

Run:

```bash
python scripts/convert_torch_toy.py --output ToyModel.mlpackage
```

The script:

- imports `torch` and `coremltools` lazily and prints a clear dependency message if either is missing;
- traces a tiny eval-mode module;
- converts with `ct.TensorType(name="input", shape=(1, 3))`;
- defaults to an ML program targeting iOS15 and skips model loading for host safety;
- refuses to overwrite an existing package unless `--overwrite` is provided.
