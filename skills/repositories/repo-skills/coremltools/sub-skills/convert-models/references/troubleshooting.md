# Conversion Troubleshooting

Use this reference to narrow failures before changing model semantics. If the failure is about saving, loading, compiling, prediction, metadata, or platform runtime, route to [model-io-and-prediction](../../model-io-and-prediction/). If the fix requires MIL graph surgery or custom passes, route to [mil-and-debugging](../../mil-and-debugging/).

## Fast triage

1. Print the source framework version and confirm it imports in the same environment as `coremltools`.
2. Identify whether the path is unified (`ct.convert`) or classic (`ct.converters.sklearn/xgboost/lightgbm/libsvm.convert`).
3. Set `source="pytorch"`, `source="tensorflow"`, or `source="milinternal"` explicitly if `source="auto"` fails.
4. Start with tensor inputs and `skip_model_load=True`; add image types, classifier metadata, pass pipelines, or prediction checks only after basic conversion succeeds.
5. For `mlprogram`, save as `.mlpackage`; for `neuralnetwork`, use an older target and do not set `compute_precision`.

## Dependency-gated converter is unavailable

Symptoms:

- `ImportError`, `ModuleNotFoundError`, or converter namespace is disabled.
- Error text says PyTorch, TensorFlow, scikit-learn, XGBoost, LightGBM, or LibSVM is missing or unsupported.
- `source="auto"` cannot determine the framework even though the artifact path exists.

Fixes:

- Install the source framework in the active conversion environment and retry a minimal import.
- For scikit-learn, XGBoost, and TensorFlow, version compatibility matters; coremltools may warn and disable a converter when the installed version is newer or older than tested.
- Do not present optional converters as verified until a tiny model for that framework converts successfully in the target environment.

## Source auto-detection fails

Typical error:

```text
Unable to determine the type of the model, i.e. the source framework.
```

Fixes:

- Pass `source="pytorch"`, `source="tensorflow"`, or `source="milinternal"` explicitly.
- Ensure the source package is installed; auto-detection only tries frontends whose dependencies are importable.
- For PyTorch, pass a TorchScript object/path or supported `ExportedProgram`, not a raw `torch.nn.Module`.
- For TensorFlow, use a supported Keras model, HDF5 path, SavedModel directory, concrete function list, graph, or graph file.

## PyTorch TorchScript input errors

Typical errors:

```text
Expected argument "inputs" for TorchScript models not provided
Input should be a list/tuple (or nested lists/tuples) of TensorType or ImageType
```

Fixes:

- Trace or script the model first; do not pass a raw `torch.nn.Module`.
- Provide `inputs=[ct.TensorType(name="...", shape=(...))]` or `inputs=[ct.ImageType(...)]`.
- Match the number and nesting of `inputs` to the traced model's positional inputs.
- Put the source module in `.eval()` mode before tracing.

## PyTorch export conversion errors

Fixes:

- Use a PyTorch version with the export API expected by coremltools.
- Prefer models that already work through TorchScript before trying the newer export path.
- Do not pass `inputs` unless you need `ImageType`, `EnumeratedShapes`, custom names, or custom dtypes.
- If dynamic shapes fail, express them in `torch.export` first; only use `ct.RangeDim`/`EnumeratedShapes` overrides when the export graph supports the same dynamism.

## TensorFlow name and artifact errors

Symptoms:

- Input/output name mismatch.
- Converter stops before or after a requested output node.
- Keras/SavedModel/HDF5 artifact loads in TensorFlow but conversion still fails.

Fixes:

- For TensorFlow, names in `TensorType`/`ImageType` must match placeholders or graph tensors. Do not use arbitrary public names during conversion; rename features after conversion if needed via model utilities.
- Run a source-framework prediction first to prove the Keras/SavedModel/HDF5 artifact is loadable.
- Convert concrete functions as a list, for example `ct.convert([concrete_function], ...)`.
- If unsupported TensorFlow ops appear, simplify the model, freeze/export a smaller subgraph, or route MIL/custom-op work to [mil-and-debugging](../../mil-and-debugging/).

## Input/output typing errors

Symptoms and fixes:

| Error pattern | Fix |
| --- | --- |
| Duplicate input names | Give each `TensorType`/`ImageType` a unique `name`, or omit names only where inference is allowed. |
| `inputs` must be list | Wrap the input descriptors in a list even for one input. |
| Output shape specified | Do not set `shape` on `outputs`; output shapes are inferred. |
| Output `ImageType` has scale/bias/channel_first | For output images, keep `scale=1.0`, `bias` unset/zero, and `channel_first=None`. |
| Float16 input/output rejected | Set `minimum_deployment_target` at least iOS16/macOS13/watchOS9/tvOS16 or use float32. |
| Int8 input/output rejected | Use a deployment target that supports int8 typed I/O or choose a wider dtype. |
| Rank-0 or `None`/`-1` dims | Use valid positive dimensions or `ct.RangeDim`; for `mlprogram`, set a finite `upper_bound`. |

## Deployment target and format conflicts

Typical errors:

```text
When 'convert_to' is mlprogram, the minimum deployment target must be at least iOS15/macOS12/watchOS8/tvOS15
If minimum deployment target is iOS15/macOS12/watchOS8/tvOS15 or higher, then 'convert_to' cannot be neuralnetwork
compute_precision is only supported for mlprogram target
```

Fixes:

- Modern target: `convert_to="mlprogram"`, target iOS15/macOS12 or newer, save as `.mlpackage`.
- Older target: `convert_to="neuralnetwork"` or target iOS14/macOS11 or older, omit `compute_precision`.
- If in doubt, specify both target and format explicitly and keep them compatible.

## Precision or numerical mismatch

Symptoms:

- Converted model has larger error than expected.
- Float16 default changes borderline predictions.

Fixes:

- Use `compute_precision=ct.precision.FLOAT32` for ML programs.
- Use `ct.transform.FP16ComputePrecision(op_selector=...)` to keep sensitive ops in float32.
- Compare outputs with tolerances appropriate for float16 and preprocessing differences.
- Verify image `scale`, `bias`, color layout, and channel order before blaming converter math.

## Unsupported ops or graph patterns

Fixes:

- Re-export the source graph from inference mode and remove training-only branches.
- For PyTorch trace, avoid data-dependent control flow or use a different capture path.
- Set `debug=True` for additional unsupported-op reporting.
- Try a smaller submodule to isolate the unsupported op.
- If the solution requires custom MIL ops, composite rewrites, or graph pass debugging, route to [mil-and-debugging](../../mil-and-debugging/).

## `pass_pipeline` errors

Symptoms:

- Pass name is not registered.
- A pass option is attached to a pass that is not in the selected pipeline.
- Conversion changes unexpectedly after disabling default passes.

Fixes:

- Start from `ct.PassPipeline()` or `ct.PassPipeline.DEFAULT`, then remove one pass at a time.
- Use exact pass names such as `"common::fuse_conv_batchnorm"`.
- If setting options, ensure the pass remains in `pipeline.passes`.
- Treat `ct.PassPipeline.EMPTY` as a debugging tool, not a default production choice.

## `states` errors

Symptoms:

- Error says `states` is only valid with PyTorch.
- Error says `inputs` cannot contain `StateType`.
- Stateful conversion succeeds but runtime state names do not work.

Fixes:

- Use `states=[ct.StateType(...)]`, not `inputs=[ct.StateType(...)]`.
- Match each `StateType.name` exactly to a TorchScript `named_buffers()` key.
- Use a sufficiently new deployment target such as iOS18/macOS15 for stateful models.
- Do not set `name` or `default_value` on the wrapped `TensorType`.

## Package and save-extension errors

Symptoms:

```text
`package_dir` must have extension .mlpackage
For an ML Program, extension must be .mlpackage
```

Fixes:

- Use `package_dir="Model.mlpackage"` only with a `.mlpackage` suffix.
- Save ML programs as `.mlpackage`, not `.mlmodel`.
- For detailed save/load/predict behavior, route to [model-io-and-prediction](../../model-io-and-prediction/).

## Classic converter issues

### scikit-learn

- Confirm the installed scikit-learn version is supported by coremltools.
- Pipelines convert only if all steps are supported.
- Use `input_features` to define public feature names and grouped array inputs.
- Classifier output names are a pair: top class and scores/probabilities.

### XGBoost

- Pass `mode="classifier"` for classifiers; default is regressor.
- Provide `class_labels` and/or `n_classes` when class count cannot be inferred.
- Feature names must match training feature order.

### LightGBM

- Categorical `"=="` splits are unsupported; one-hot encode categorical features before training.
- Default `mode` is classifier; set `mode="regressor"` for regression models.
- Provide feature names explicitly when model metadata is incomplete.

### LibSVM

- Install the `libsvm` Python package expected by coremltools.
- Use `input_names="features"` plus `input_length=N` for one array input.
- Use a list of `input_names` for separate scalar features.
- Probability output exists only for SVM models trained with probability estimates.

## Platform prediction surprises after conversion

Conversion can succeed on hosts where Core ML prediction is unavailable or where the target model type cannot be loaded. Use `skip_model_load=True` for conversion-only workflows and route prediction setup to [model-io-and-prediction](../../model-io-and-prediction/).
