---
name: workflows
description: "Compose and validate Earth2Studio deterministic and
  prognostic-plus-diagnostic inference workflows with coordinate-aware inputs,
  outputs, devices, checkpoints, and offline protocol checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Earth2Studio workflows

Use this skill when a task needs a concrete Earth2Studio inference pipeline built
from a prognostic model, a data source, an IO backend, and optionally a
coordinate-compatible diagnostic model. It owns the deterministic and
prognostic-plus-diagnostic paths exposed by `earth2studio.run`; it does not own
ensemble orchestration, data-only retrieval, detailed backend selection, or
remote serving.

## Decide the path

1. Clarify initialization times, forecast horizon, variables, spatial domain,
   output format, and CPU/GPU constraints. Use ISO-8601 strings, `datetime`, or
   `np.datetime64` values for `time`.
2. Select a prognostic class whose `input_coords()` can be supplied by the
   selected `DataSource` or `ForecastSource`. Inspect its `output_coords()` to
   learn the model step and output variables; do not assume all models use the
   same grid or lead time.
3. Add a diagnostic only when a derived field is required. Its
   `input_coords()` must be mappable from each prognostic output, and its
   `output_coords()` determines the variables written by `run.diagnostic`.
4. Select an IO object and initialize it outside the workflow. The run function
   mutates and returns the same IO object. See [API reference](references/api-reference.md)
   for the narrow IO contract and supported public backend names.
5. Calculate `nsteps` from the model's advertised lead-time increment. A run
   writes the initial state plus `nsteps` forecast steps, so the lead-time axis
   has `nsteps + 1` entries.

## Load components

For a packaged model, use the class's public loading pair; the package handle
is lightweight, while `load_model` may access remote or cached assets:

```python
from earth2studio.models.px import <PrognosticClass>

prognostic = <PrognosticClass>.load_model(
    <PrognosticClass>.load_default_package()
)
```

Use the analogous pair from `earth2studio.models.dx` for a diagnostic. Model
classes can require targeted optional extras and model-specific hardware; do
not recommend an extra until the chosen class's installation notes are known.
A network-free smoke path uses `Persistence`, `Identity`, `Random`, and
`ZarrBackend`; it checks protocol and coordinate behavior without model
weights. See [workflow recipes](references/workflows.md).

## Run deterministic inference

Construct `data` and `io`, inspect `prognostic.input_coords()`, then call:

```python
from earth2studio import run

result = run.deterministic(
    time=["2024-01-01T00:00:00"],
    nsteps=8,
    prognostic=prognostic,
    data=data,
    io=io,
    output_coords=output_coords,  # omit or use OrderedDict({}) for all output
    device=device,                # None selects CUDA when available, else CPU
    verbose=True,
    checkpoint=checkpoint,         # optional checkpoint manager/session
)
```

`run.deterministic` fetches the prognostic initial-condition variables and
lead times, maps them to the model grid, iterates from the initial state,
applies `output_coords` at each step, and calls `io.write`. It returns `io`, not a new
result wrapper. Use a small `nsteps` and `verbose=False` for a smoke run.

## Run diagnostic inference

Keep the same initial-condition and prognostic setup, load a diagnostic, and
call `run.diagnostic(time, nsteps, prognostic, diagnostic, data, io, ...)`.
The workflow maps each prognostic step to `diagnostic.input_coords()`, invokes
the diagnostic, then maps to `output_coords` before writing. Its output is the
diagnostic result; it does not retain the prognostic fields in the output
backend. If both are required, compose a custom workflow rather than assuming
this built-in path stores both.

## Coordinate and horizon checks

Before a live run:

- Compare `data` variables with `prognostic.input_coords()["variable"]`.
- Read the model's `lead_time` increment and use an integer `nsteps`.
- Preserve coordinate key order: keys describe tensor dimensions. Common keys
  are `batch`, `time`, `lead_time`, `variable`, `lat`, and `lon`.
- Keep `output_coords` a subset of produced dimensions. Variable restrictions
  must name produced variables; spatial restrictions may select or nearest-map
  numeric 1-D coordinates. Empty arrays are used by model protocols for free
  dimensions; do not use empty output overrides unless the backend contract
  explicitly permits them.
- For a diagnostic, check every required diagnostic dimension and variable can
  be mapped from the prognostic output. Exact grid handshakes may still be
  required by a model even where the workflow can numerically map coordinates.
- Run the bundled offline checker before spending network or GPU resources:
  `python path/to/check_workflow_config.py --config workflow.json`.

See [workflows](references/workflows.md) for runnable CPU mock examples and
[troubleshooting](references/troubleshooting.md) for recovery by failure class.

## Boundaries and omissions

This sub-skill intentionally omits `run.ensemble` and perturbation/batch-size
orchestration, a catalog of IO backend options, custom model implementation,
full data-source selection, serving clients, and model-weight download
procedures. It names public interfaces and targeted-extra constraints but does
not claim exhaustive model, data, or backend coverage. Use the sibling skill
for deterministic forecast selection when the task is only model/data/horizon
recommendation; use data-fetch or installation guidance for those concerns.

## Handoff checks

Report the selected workflow, model/data/diagnostic classes, initialization
times, `nsteps` and implied lead-time horizon, output coordinate restriction,
device, IO backend, whether weights/data are downloaded, and the validation
performed. Preserve unresolved coordinate, optional-extra, credential, and
hardware limits instead of presenting a smoke test as a scientific forecast.

- [API and signatures](references/api-reference.md)
- [Workflow recipes and validation](references/workflows.md)
- [Predictable failures](references/troubleshooting.md)
- [Offline configuration checker](scripts/check_workflow_config.py)
