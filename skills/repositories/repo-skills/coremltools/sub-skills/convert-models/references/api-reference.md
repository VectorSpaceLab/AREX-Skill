# Converter API Reference

This reference summarizes the runtime conversion surface for future agents. Optional source frameworks are dependency-gated; do not claim a converter path is verified until the corresponding package imports and a small native conversion runs in the active environment.

## Unified converter: `ct.convert`

```python
ct.convert(
    model,
    source="auto",
    inputs=None,
    outputs=None,
    classifier_config=None,
    minimum_deployment_target=None,
    convert_to=None,
    compute_precision=None,
    skip_model_load=False,
    compute_units=ct.ComputeUnit.ALL,
    package_dir=None,
    debug=False,
    pass_pipeline=None,
    states=None,
)
```

Use `ct.convert` for TensorFlow, PyTorch, and MIL source models. It returns either a `coremltools.models.MLModel` or a MIL `Program` when `convert_to="milinternal"`.

### Source selection

| `source` | Use for | Key constraints |
| --- | --- | --- |
| `"auto"` | First attempt when source package and artifact are unambiguous. | If detection fails, pass `source="tensorflow"`, `source="pytorch"`, or `source="milinternal"` explicitly. |
| `"pytorch"` | TorchScript object/path or `torch.export.ExportedProgram`. | TorchScript requires `inputs`; `ExportedProgram` carries shapes/names/dtypes unless overriding with image/enumerated/custom typing. Requires PyTorch. |
| `"tensorflow"` | TensorFlow 1/2 graph, Keras, HDF5, SavedModel, concrete function, or GraphDef. | Names in `inputs`/`outputs` must match graph tensors/nodes. Requires TensorFlow. |
| `"milinternal"` | Existing MIL `Program`. | Use this sub-skill only for conversion. Build or debug the MIL graph via [mil-and-debugging](../../mil-and-debugging/). |

If the error says the converter cannot determine the source framework, the usual causes are missing optional dependency, unsupported artifact type, or a need to set `source` explicitly.

## Input and output type helpers

### `ct.TensorType`

```python
ct.TensorType(name=None, shape=None, dtype=None, default_value=None)
```

Use for `MLMultiArray`-style tensor inputs/outputs.

- PyTorch TorchScript inputs require `shape`; `name` controls the Core ML input name.
- TensorFlow can often infer shape/name, but static shapes improve optimization and explicit names must match source graph placeholders.
- `dtype` may be a NumPy dtype or MIL type. Float16 typed inputs/outputs require deployment targets at least iOS16/macOS13/watchOS9/tvOS16. Int8 typed inputs/outputs require newer deployment targets that support int8.
- `default_value` makes an input optional; it must be a NumPy array with the same value in every element and cannot be used with `EnumeratedShapes`.
- For flexible shapes, use `ct.RangeDim`, `ct.Shape`, or `ct.EnumeratedShapes`. For `mlprogram`, every `RangeDim` must have a finite positive `upper_bound`.

### `ct.ImageType`

```python
ct.ImageType(
    name=None,
    shape=None,
    scale=1.0,
    bias=None,
    color_layout=ct.colorlayout.RGB,
    channel_first=None,
    grayscale_use_uint8=False,
)
```

Use when the Core ML interface should accept images instead of raw multiarrays.

- `color_layout`: `ct.colorlayout.RGB`, `BGR`, `GRAYSCALE`, or `GRAYSCALE_FLOAT16`.
- `channel_first`: default differs by source family: PyTorch is channel-first; TensorFlow is channel-last. Set it explicitly when model conventions are not obvious.
- `scale` and `bias` encode preprocessing into the Core ML input. For RGB/BGR, `bias` is usually a length-3 list; for grayscale, it is a scalar.
- `grayscale_use_uint8=True` applies only to grayscale input and requires a sufficiently new deployment target; it can restrict available MIL ops.
- For output `ImageType`, do not set a shape, keep `scale=1.0`, keep `bias` unset/zero, and leave `channel_first=None`.

### `ct.ClassifierConfig`

```python
ct.ClassifierConfig(
    class_labels,
    predicted_feature_name="classLabel",
    predicted_probabilities_output=None,
)
```

Use when the converted model output is a probability distribution and should be exposed as a classifier.

- `class_labels` may be a list of strings/ints or a file path containing labels.
- `predicted_feature_name` names the top-label output.
- `predicted_probabilities_output` should match the source output that contains probabilities; if omitted, the converter assumes the last output.

## Deployment target and model format

| Goal | Typical arguments | Notes |
| --- | --- | --- |
| Modern ML program | `convert_to="mlprogram"` or no format args | Default when neither `convert_to` nor `minimum_deployment_target` is specified. Minimum runtime is iOS15/macOS12/watchOS8/tvOS15. Save as `.mlpackage`. |
| Legacy neural network | `convert_to="neuralnetwork"` or `minimum_deployment_target=ct.target.iOS14` or older | Required for older OS targets. `compute_precision` must be `None`. Save as `.mlmodel` or `.mlpackage`. |
| Inspectable MIL program | `convert_to="milinternal"` | Returns a MIL `Program` for inspection/debugging, not a deployable model. Route detailed MIL work to [mil-and-debugging](../../mil-and-debugging/). |

Compatibility rules:

- `convert_to="mlprogram"` is incompatible with deployment targets below iOS15/macOS12/watchOS8/tvOS15.
- `convert_to="neuralnetwork"` is incompatible with deployment targets at or above iOS15/macOS12/watchOS8/tvOS15.
- If both `convert_to` and `minimum_deployment_target` are omitted, the converter chooses `mlprogram` with the oldest deployment target that supports it.

## Precision and compute units

### `compute_precision`

Applies to `mlprogram` only.

- `None`: default behavior; for `mlprogram`, the converter inserts float16 compute casts by default.
- `ct.precision.FLOAT16`: produce a float16 ML program where supported.
- `ct.precision.FLOAT32`: preserve float32 compute when numerical accuracy is more important than size/performance.
- `ct.transform.FP16ComputePrecision(op_selector=...)`: customize which ops are cast to float16.

Do not pass `compute_precision` when converting to `neuralnetwork`.

### `compute_units`

Controls how the returned `MLModel` is loaded for prediction after conversion:

- `ct.ComputeUnit.ALL`
- `ct.ComputeUnit.CPU_ONLY`
- `ct.ComputeUnit.CPU_AND_GPU`
- `ct.ComputeUnit.CPU_AND_NE` on supported macOS versions

For deterministic conversion smoke checks, `CPU_ONLY` is often safest. Prediction availability and compute-unit behavior are handled by [model-io-and-prediction](../../model-io-and-prediction/).

## Conversion-side storage and loading controls

- `skip_model_load=True`: avoids compiling/loading the model after conversion. Use this on platforms that cannot load the produced model type, or when converting a newer model type on an older macOS. The returned object can still be saved but cannot be used for prediction until loaded on a supported platform.
- `package_dir="... .mlpackage"`: tells the converter where to place the temporary/saved package used during conversion. The path must end in `.mlpackage`.
- `debug=True`: useful when converter frontend failures should print additional unsupported-op information.

## Graph pass pipeline

`pass_pipeline` accepts a `ct.PassPipeline` object.

Common patterns:

```python
pipeline = ct.PassPipeline()
pipeline.remove_passes({"common::fuse_conv_batchnorm"})
mlmodel = ct.convert(source_model, pass_pipeline=pipeline)
```

```python
pipeline = ct.PassPipeline()
pipeline.set_options("common::const_elimination", {"skip_const_by_size": "1e6"})
mlmodel = ct.convert(source_model, pass_pipeline=pipeline)
```

Predefined pipelines include:

- `ct.PassPipeline.EMPTY`: run no graph passes.
- `ct.PassPipeline.CLEANUP`: run cleanup passes only.
- `ct.PassPipeline.DEFAULT_PRUNING`: conversion-time sparsification for already sparse weights.
- `ct.PassPipeline.DEFAULT_PALETTIZATION`: conversion-time palettization for already palettized weights.

For custom pass authoring and MIL graph inspection, route to [mil-and-debugging](../../mil-and-debugging/). For compression after conversion, route to [optimize-models](../../optimize-models/).

## PyTorch stateful conversion

`states` creates a stateful `mlprogram` model from TorchScript state buffers:

```python
states = [
    ct.StateType(
        wrapped_type=ct.TensorType(shape=(1, 2)),
        name="state_1",
    )
]
mlmodel = ct.convert(
    traced_model,
    inputs=[ct.TensorType(name="x", shape=(1, 2))],
    states=states,
    minimum_deployment_target=ct.target.iOS18,
)
```

Constraints:

- `states` is PyTorch-only.
- `ct.StateType.name` must match a key from the TorchScript model's `named_buffers()`.
- Do not put `StateType` inside `inputs`; pass state descriptors through the separate `states` argument.
- The wrapped `TensorType` must not set `name` or `default_value`.

## Classic converters

Classic converters do not use `ct.convert` and do not accept `TensorType`, `ImageType`, `compute_precision`, `pass_pipeline`, or `states`. They return `MLModel` objects or specs for tree/SVM/classic ML workflows.

| Source | Entry point | Dependency gate | Core arguments |
| --- | --- | --- | --- |
| scikit-learn | `ct.converters.sklearn.convert(sk_obj, input_features=None, output_feature_names=None)` | Compatible `scikit-learn`; converter disables itself when missing or unsupported. | `sk_obj` may be a supported estimator, pipeline, or list. `input_features` may be a string, list, dict, or `(name, datatype)` tuples. `output_feature_names` depends on transformer/regressor/classifier output type. |
| XGBoost | `ct.converters.xgboost.convert(model, feature_names=None, target="target", force_32bit_float=True, mode="regressor", class_labels=None, n_classes=None)` | `xgboost`. | Use `mode="classifier"` with `class_labels`/`n_classes` as needed; otherwise default is regressor. |
| LightGBM | `ct.converters.lightgbm.convert(model, feature_names=None, target="target", force_32bit_float=True, mode="classifier", class_labels=None, n_classes=None)` | `lightgbm`. | Categorical-feature `"=="` splits are not supported; one-hot encode categorical inputs before training. |
| LibSVM | `ct.converters.libsvm.convert(model, input_names="input", target_name="target", probability="classProbability", input_length="auto")` | `libsvm`. | `model` may be a LibSVM model or saved model path. Use a single `input_names` string for array input, or a list for separate scalar inputs. |

## Validate before save or predict

Before handing the model to save/load/predict workflows:

1. Confirm the returned object is an `MLModel` unless you explicitly requested `convert_to="milinternal"`.
2. Inspect input/output names and shapes from the model spec or model description.
3. Confirm deployment target and model type match the requested platform.
4. On macOS with supported runtime, compare a small source-model output against `mlmodel.predict(...)` using loose tolerances appropriate for float16 if applicable.
5. Then route persistence and prediction details to [model-io-and-prediction](../../model-io-and-prediction/).
