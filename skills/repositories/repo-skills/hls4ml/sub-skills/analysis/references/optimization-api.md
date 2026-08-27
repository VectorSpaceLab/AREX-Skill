# Hardware-aware optimization API

The optimization API is for pruning and weight sharing before conversion or before regenerating a tuned hls4ml project. It is not a replacement for precision profiling, C simulation, or backend synthesis reports.

## Dependency and import caveats

The optional model-optimization extra was not installed during drafting because `ortools==9.4.1874` did not resolve for Python 3.11. API imports can still be visible, but runtime execution that needs the knapsack solver or tuner stack may fail without the optimization dependencies.

If runtime verification is required, prepare a separate Python 3.10-compatible environment or an adjusted dependency set that resolves the pinned `ortools` and tuner requirements. Do not silently downgrade the claim to verified if the optimization loop was not executed.

In this checkout, the public functions are exported from the `dsp_aware_pruning` subpackage, not from the empty top-level `hls4ml.optimization` package:

```python
from hls4ml.optimization.dsp_aware_pruning import optimize_keras_model_for_hls4ml
from hls4ml.optimization.dsp_aware_pruning.keras import optimize_model
from hls4ml.optimization.dsp_aware_pruning.attributes import (
    get_attributes_from_keras_model,
    get_attributes_from_keras_model_and_hls4ml_config,
)
```

## Main entry points

Use the hls4ml-aware wrapper when you need hardware attributes such as reuse factor, strategy, output precision, or Vivado DSP estimation:

```python
optimized_model = optimize_keras_model_for_hls4ml(
    keras_model,
    hls_config,
    objective,
    scheduler,
    X_train,
    y_train,
    X_val,
    y_val,
    batch_size,
    epochs,
    optimizer,
    loss_fn,
    validation_metric,
    increasing,
    rtol,
)
```

Use the lower-level Keras optimizer when you have already built `model_attributes`:

```python
model_attributes = get_attributes_from_keras_model(keras_model)
optimized_model = optimize_model(
    keras_model,
    model_attributes,
    objective,
    scheduler,
    X_train,
    y_train,
    X_val,
    y_val,
    batch_size,
    epochs,
    optimizer,
    loss_fn,
    validation_metric,
    increasing,
    rtol,
)
```

Common objective and scheduler imports:

```python
from hls4ml.optimization.dsp_aware_pruning.objectives import ParameterEstimator
from hls4ml.optimization.dsp_aware_pruning.objectives.gpu_objectives import GPUFLOPEstimator
from hls4ml.optimization.dsp_aware_pruning.objectives.vivado_objectives import (
    VivadoDSPEstimator,
    VivadoFFEstimator,
    VivadoMultiObjectiveEstimator,
)
from hls4ml.optimization.dsp_aware_pruning.scheduler import PolynomialScheduler
```

## hls4ml config requirements

For the hls4ml-aware wrapper, build a name-granular config and keep hardware knobs explicit:

```python
hls_config = hls4ml.utils.config_from_keras_model(
    keras_model,
    granularity="name",
    default_precision="fixed<16,6>",
    default_reuse_factor=4,
    backend="Vivado",
)
hls_config["IOType"] = "io_parallel"
hls_config["Model"]["Strategy"] = "Resource"
```

Why this matters:

- The attribute extractor reads `IOType`, `Model.ReuseFactor`, `Model.Strategy`, `Model.Precision`, layer-name `ReuseFactor`, layer-name `ParallelizationFactor`, and `Precision.weight`/`Precision.result`.
- Only supported Keras layers can become optimizable; unsupported layers remain pass-through.
- Vivado DSP/FF/multi-objective estimators need the hls4ml-specific attributes to estimate hardware targets.
- For DSP-focused synthesis claims, regenerate hls4ml from the optimized model and use backend evidence; optimization metrics alone are not HLS report evidence.

## Runtime guardrails

- `scheduler` must be an `OptimizationScheduler` instance, not a string.
- `epochs` must be greater than `rewinding_epochs`.
- `ranking_metric` must be one of the metrics supported by the optimizer implementation.
- Training and validation arrays are consumed directly; this is not a no-training helper.
- The optimizer saves temporary weights/results under its `directory` argument. Pick a safe user-approved working directory outside the runtime skill tree.
- If optional dependencies such as `ortools` or tuner packages are missing, document the dependency block instead of presenting source-documented examples as verified runtime results.

## When to use a different sub-skill

- If the user only wants to edit fixed-point types or diagnose accuracy loss, use `precision-and-bit-exact.md` and `profiling.md` first.
- If the user wants HLS resource utilization after pruning, route synthesis/report execution to `backends`.
- If pruning requires unsupported custom layers or objective authoring, route custom extension work to `extensions`.
