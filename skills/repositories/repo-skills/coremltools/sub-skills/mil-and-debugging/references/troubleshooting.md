# MIL and debugging troubleshooting

Use this reference to map advanced coremltools symptoms to the smallest next action. Keep routine conversion, artifact I/O, and compression issues in their dedicated sibling sub-skills unless the failure clearly requires MIL/pass/debugger internals.

## Fast stage classifier

| Symptom | Likely stage | First action |
| --- | --- | --- |
| Builder code raises before `ct.convert` | MIL construction/type inference | Print the program, check op input names, const values, rank, dtype, and symbolic shapes. |
| `ct.convert` fails only with default passes | Graph pass pipeline | Retry with `ct.PassPipeline.EMPTY`, then `CLEANUP`, then bisect default passes. |
| `convert_to="mlprogram"` fails but `neuralnetwork` works | ML Program backend/save/native package support | Check BlobWriter/native messages; try a matching coremltools wheel or supported runtime. |
| Error mentions deployment target/specification version | Deployment compatibility | Raise `minimum_deployment_target` or replace newer MIL ops/patterns. |
| Model saves but `predict` fails | Core ML runtime/prediction | Verify macOS/runtime availability, compute units, input names, dtypes, and shapes. |
| Inspector/validator says it only supports ML Program | Experimental debugger scope | Convert with `convert_to="mlprogram"`; do not use these utilities on neural networks. |

## Builder and MIL program errors

Common causes:

- The number of `input_specs` does not match the decorated function arguments.
- An op receives positional inputs; MIL Builder ops require named inputs such as `mb.add(x=a, y=b)`.
- A Python value containing symbolic dimensions is passed where a concrete const is required.
- Input shape rank is invalid for the op, or rank-0 input is used without explicit support.
- Dtypes differ from op expectations, such as using floating-point inputs for integer indexing or int tensors for fp-only ops.
- An output is a Python container or value rather than a MIL `Var` or list/tuple of `Var` objects.

Actions:

```python
print(prog)
print(prog.functions.keys())
print(prog.functions["main"])
```

Then shrink to the smallest Builder program with the same op, shape, dtype, and const values. Give every suspect op a stable `name` so later conversion, inspector, and submodel extraction steps can target it.

## PassPipeline errors

### Unknown pass name

Cause: the pass name is not registered or the namespace is wrong.

Actions:

```python
print(ct.PassPipeline.list_available_pipelines())
print(ct.PassPipeline.DEFAULT.passes)
```

Use exact registry keys such as `common::dead_code_elimination` or `common::const_elimination`.

### Option set for a pass that is not in the pipeline

Cause: `pipeline.set_options(...)` attaches options, but validation requires the pass to also be present in `pipeline.passes`.

Actions:

```python
pipeline = ct.PassPipeline.DEFAULT
if "common::const_elimination" in pipeline.passes:
    pipeline.set_options("common::const_elimination", {"skip_const_by_size": "1000000"})
```

### Default pipeline fails, empty pipeline works

Cause: a graph rewrite changed or exposed an invalid pattern.

Actions:

1. Try `ct.PassPipeline.CLEANUP` to separate cleanup passes from common optimizations.
2. Bisect `ct.PassPipeline.DEFAULT.passes` by assigning prefixes to `ct.PassPipeline.EMPTY.passes`.
3. Remove the isolated pass only as a workaround; also inspect the MIL pattern that triggered it.
4. If large constants are involved, try `common::const_elimination` options such as `skip_const_by_size`.

## ML Program BlobWriter or native package errors

Symptoms may mention `BlobWriter`, `libmilstoragepython`, `libcoremlpython`, native package loading, package writer failures, or a fatal native crash during import/conversion/save.

Meaning:

- Pure Python MIL construction may be fine.
- ML Program backend/save needs native coremltools components.
- The installed wheel, Python version, operating system, or binary dependencies may be incompatible.

Actions:

1. Run the smoke script with the neural network backend:
   ```bash
   python scripts/mil_smoke.py --convert-to neuralnetwork --output mil_smoke.mlmodel
   ```
2. Run the ML Program smoke separately:
   ```bash
   python scripts/mil_smoke.py --convert-to mlprogram --output mil_smoke.mlpackage
   ```
3. If only ML Program fails, treat it as backend/native packaging rather than a source-model conversion bug.
4. Use a supported coremltools build for the current Python and platform, or run ML Program save/debug work in a compatible macOS/runtime environment.
5. Do not use prediction or experimental intermediate-output utilities as proof of conversion correctness on unsupported runtimes.

The bundled smoke script runs conversion in a child process by default so native crashes are reported as signals instead of taking down the parent process.

## Prediction and runtime errors

Core ML prediction is supported on macOS. On other systems, model conversion and save can succeed while `MLModel.predict`, compiled-model loading, compute-plan access, or intermediate-output retrieval fails.

Actions:

- Treat `predict` failures separately from conversion failures.
- Use `ct.ComputeUnit.CPU_ONLY` when comparing numeric behavior and when GPU/Neural Engine partitioning is not the subject of the test.
- Use the model's sanitized input names from the saved spec or converted model description; names containing characters such as `/` may be sanitized during conversion.
- Match input dtype and shape exactly. Convert NumPy inputs to the expected dtype before prediction.
- For stateful models, verify target OS/runtime support and pass the state object returned by `make_state()`.

## Experimental inspector, validator, and comparator issues

### `MLModelInspector only supports ML program`

Convert the model as an ML Program:

```python
mlmodel = ct.convert(prog, convert_to="mlprogram", compute_precision=ct.precision.FLOAT32)
```

### Invalid output name

Use available output names from the inspector:

```python
inspector = MLModelInspector(model=mlmodel)
print(inspector.output_names)
```

Then request only names in that list. Constants may be ignored depending on `ignore_const_ops`.

### Retrieval is slow or memory-heavy

Lower `num_predict_intermediate_outputs` so each prediction call exposes fewer intermediates. This can be slower but reduces output pressure.

### Comparator results are confusing

`MLModelComparator` expects reference and target models derived from the same source graph. If comparing unrelated models, op correspondence is not meaningful. For precision debugging, create reference and target models from the same MIL/source model while changing only precision or compute settings.

## Custom and composite operator errors

### Unsupported source op during conversion

Prefer a composite registration that rewrites the source op into existing MIL Builder ops. Verify the composite function is imported before calling `ct.convert`.

### Custom layer converts but fails in app/runtime

Check the custom op binding:

- `class_name` exactly matches the Swift custom layer class.
- `input_order` matches the order consumed by the Swift implementation.
- `parameters` names match static attributes expected by Swift.
- `type_inference` returns shapes and dtypes matching runtime output.
- `convert_to="neuralnetwork"` is used; custom layers are not available for ML Programs.

### Custom op used when a composite would work

Rewrite it as a composite. Composite ops compile into supported Core ML operations and are more portable across backends and compute units.

## Deployment target errors

Symptoms include messages that a model requires a later specification version than the provided minimum deployment target.

Actions:

```python
for target in [ct.target.iOS15, ct.target.iOS16, ct.target.iOS17, ct.target.iOS18]:
    try:
        model = ct.convert(prog, convert_to="mlprogram", minimum_deployment_target=target)
        print("works", target)
    except Exception as exc:
        print("fails", target, exc)
```

If the lowest required target is too new, replace newer ops/patterns or choose another backend. Do not suppress the error by omitting the target if the downstream deployment actually requires an older OS.

## Precision regressions

Symptoms include output mismatch only for ML Program default precision, only on GPU/Neural Engine, or only after conversion optimizations.

Actions:

1. Convert an ML Program with `compute_precision=ct.precision.FLOAT32`.
2. Convert a second model with the intended precision settings.
3. Compare model outputs if prediction is available.
4. Use `MLModelComparator` to find failing operations when both models are ML Programs and runtime output retrieval is available.
5. Use selective `ct.transform.Float16ComputePrecision(...)` to preserve float32 for sensitive ops.
6. For neural networks, use CPU-only runtime as a float32 diagnostic, not as proof that all deployed compute units will match.

## Submodel extraction failures

Common causes:

- Requested `outputs` name does not exist in the function.
- Duplicate output names were passed.
- Requested `inputs` cannot reach the selected outputs.
- Neural network model was loaded from disk; neural network extraction requires the in-memory converted model.

Actions:

- Use explicit op/output names in the original MIL program.
- Print or inspect output names before extraction.
- Start with only `outputs=[...]`; add `inputs=[...]` after confirming reachability.
- For ML Programs loaded from disk, keep the associated weights directory/package intact.
