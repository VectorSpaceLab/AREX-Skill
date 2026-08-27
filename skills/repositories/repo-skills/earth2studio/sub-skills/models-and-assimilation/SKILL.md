---
name: models-and-assimilation
description: "Route Earth2Studio prognostic, diagnostic, and data-assimilation
  model families, load optional model packages safely, and validate tensor or
  observation-schema contracts without guessing model support."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Models and assimilation

Use this sub-skill when a task must select or wire an Earth2Studio model, inspect
its coordinate contract, load a packaged checkpoint, use a downscaler or
nowcaster, or assimilate observations. It is a routing and contract skill: it
does not replace the run workflows, data-source catalog, IO setup, or model
checkpoint acquisition.

## Route before running

1. Classify the component as **prognostic** (`earth2studio.models.px`),
   **diagnostic** (`earth2studio.models.dx`), or **assimilation**
   (`earth2studio.models.da`). A prognostic advances a state; a diagnostic
   transforms one state without time integration; an assimilation consumes
   observations and may update a background state.
2. Read the model's `input_coords()` before fetching or constructing data. Treat
   `output_coords(input_coords)` as the authoritative output schema; do not
   infer variable order, spatial dimensions, lead-time spacing, or history
   length from a model name.
3. Choose the narrow optional extra for the selected class. Check device,
   Python version, compiled extensions, and package conflicts before calling
   `load_model`. See [API reference](references/api-reference.md).
4. Verify the contract with the bundled offline fixture first:
   `python path/to/check_model_contract.py --tiny-fixture`. It does not import
   Earth2Studio, access credentials, download weights, or require a GPU.
5. For a real model, construct the package and inspect coordinates before
   allowing asset access. `load_default_package()` creates a package pointer;
   `load_model(package)` may fetch checkpoint assets and is outside this
   sub-skill's safe offline check.

## Minimal model contract

All three families expose `input_coords`, `output_coords`, and `to(device)`.
Prognostics additionally implement `__call__(x, coords)`,
`create_iterator(x, coords)`, and normally yield the initial condition as
iterator step zero. Diagnostics implement `__call__(x, coords)` but do not
roll a forecast. Assimilation models use DataFrame or xarray inputs and expose
`__call__`, `create_generator`, `init_coords`, `input_coords`, and
`output_coords`; concrete generator priming differs by class.

A valid call returns both data and coordinates (except concrete DA classes that
return xarray `DataArray`). Preserve coordinate ordering and move model and
input data to the same device. Use `output_coords` and explicit handshakes to
catch a wrong variable, grid, history window, or lead-time contract before an
expensive forward pass.

## Safe selection workflow

- **Global forecast:** start with a px class whose variables, grid, and native
  step match the initial condition. Ensemble-named classes and models with
  stochastic samplers have additional memory and reproducibility requirements.
- **Downscaling or derived field:** use a dx class. CorrDiff-like models can
  generate a `sample` dimension; map the prognostic output to the diagnostic's
  input schema before calling it. DLESyM coupled outputs have different valid
  atmosphere and ocean lead times; select them with the model's helpers.
- **Nowcasting:** use StormCast or StormScope variants only with their required
  regional/history and conditioning contracts. StormScope GOES and MRMS can
  be coupled, and MRMS may require GOES/GLM conditioning.
- **Seasonal or coupled Earth system:** DLESyM variants use HEALPix internally
  or a lat/lon convenience wrapper. Do not assume every lead time is valid for
  every component.
- **Assimilation:** decide whether calls are independent (stateless) or a
  sequence carries state (generator). Validate observation columns, units,
  time attributes, spatial domain, and output backend before choosing a class.

The detailed family map and representative model choices are in
[model overview](references/model-overview.md). Do not treat its lists as
exhaustive support claims.

## Loading and inspecting a model

Use the concrete exported class, not the protocol, to load a checkpoint:

```python
from earth2studio.models.px import FCN

package = FCN.load_default_package()  # package pointer; no asset read by itself
model = FCN.load_model(package)       # may access/download checkpoint files
model = model.to("cuda" if torch.cuda.is_available() else "cpu")
in_coords = model.input_coords()
out_coords = model.output_coords(in_coords)
print(in_coords)
print(out_coords)
```

For a local or remote package, the same loader accepts `Package(root)` or
`Class.from_pretrained(root)` where that class inherits `AutoModelMixin`.
Supported package roots include local paths and fsspec-backed HF, S3, and NGC
URIs. Resolve only assets required by the selected model; do not use recursive
NGC glob/find operations. Package caching and timeout behavior are summarized
in [API reference](references/api-reference.md).

## Coordinate and schema gates

Before a tensor forward pass, assert that the input tensor matches
`input_coords()` and that the requested output is a subset of
`output_coords(...)`. For state windows, preserve the model's `time` and
`lead_time` arrays; for curvilinear or HEALPix models preserve named spatial
axes rather than substituting a regular lat/lon grid.

For observation models, validate every required DataFrame field before filtering
by time. Use the model's `FrameSchema` (or `CoordSystem`) rather than a guessed
column list. Attach `request_time` when the concrete implementation requires it.
An empty observation batch is not automatically invalid: some models return an
empty/NaN analysis or an unconstrained forecast, while others require at least
one input. See [assimilation](references/assimilation.md).

## Verification and recovery

Run the offline fixture for protocol and stateful-generator behavior, then run a
small native model test only when its extra, checkpoint cache, backend, and GPU
requirements are satisfied. Keep model-download and long-running inference
explicitly opt-in. If a gate fails, use the targeted recovery in
[troubleshooting](references/troubleshooting.md), repair the schema/device/extra,
and re-check coordinates before retrying.

Use [API reference](references/api-reference.md) for exact signatures and
optional extras, [assimilation](references/assimilation.md) for DA generator
schemas, and [model overview](references/model-overview.md) for family routing.
The [offline contract checker](scripts/check_model_contract.py) is the only
bundled helper and is safe to run from any working directory.

## Deliberate limits

This skill does not catalog data sources, implement `run.deterministic`,
`run.diagnostic`, or `run.ensemble`, configure IO backends, download full model
packages, or claim that a model works on every backend. It also does not replace
model-specific upstream documentation for weights, accuracy, or production
capacity. Validate the selected class and hardware in the target environment.
