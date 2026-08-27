# Workflow recipes and validation

These recipes separate a safe offline protocol check from a real forecast. The
real path needs an installed Earth2Studio environment, a compatible data source,
and any model-specific extras and assets. Keep the same component versions for
model and data coordinate conventions.

## 1. Offline deterministic smoke run

`Persistence`, `Random`, and `ZarrBackend` are package-provided testing
components. This run uses no model package and is suitable for checking tensor
shape, coordinate mapping, output filtering, and device plumbing.

```python
from collections import OrderedDict

import numpy as np
import torch

from earth2studio.data import Random
from earth2studio.io import ZarrBackend
from earth2studio.models.px import Persistence
from earth2studio.run import deterministic

model_coords = OrderedDict(
    {
        "lat": np.arange(3),
        "lon": np.arange(4),
    }
)
# The source deliberately has one extra latitude. The workflow can select the
# model's regular 1-D coordinates during mapping.
data = Random(
    domain_coords=OrderedDict(
        {"lat": np.arange(4), "lon": np.arange(4)}
    )
)
model = Persistence(["t2m", "u10m"], model_coords)
io = ZarrBackend()

output_coords = OrderedDict(
    {
        "variable": np.array(["t2m"]),
        "lat": np.array([0, 2]),
    }
)
result = deterministic(
    ["2024-01-01T00:00:00"],
    2,
    model,
    data,
    io,
    output_coords=output_coords,
    device=torch.device("cpu"),
    verbose=False,
)
```

Expected checks after the call:

```python
assert result is io
assert result["t2m"].shape[:2] == (1, 3)  # time, initial + 2 steps
assert "u10m" not in list(result.root.array_keys())
assert np.array_equal(result["lat"][:], np.array([0, 2]))
```

This is a mechanics check only. `Random` generates random values and
`Persistence` copies the state; neither establishes forecast skill.

## 2. Offline diagnostic smoke run

Use the same source and prognostic, and add the coordinate-insensitive
`Identity` diagnostic. A real diagnostic replaces `Identity` and must advertise
compatible input/output coordinates.

```python
from earth2studio.models.dx import Identity
from earth2studio.run import diagnostic

result = diagnostic(
    ["2024-01-01T00:00:00"],
    2,
    model,
    Identity(),
    data,
    ZarrBackend(),
    output_coords=output_coords,
    device="cpu",
    verbose=False,
)
assert "t2m" in list(result.root.array_keys())
assert "u10m" not in list(result.root.array_keys())
```

The built-in diagnostic workflow writes the fields returned by the diagnostic.
It does not automatically preserve prognostic fields that the diagnostic
removed. Write a custom loop when both branches must be retained.

## 3. Real deterministic pipeline

First inspect model contracts rather than selecting a model by name alone:

```python
from earth2studio.models.px import <PrognosticClass>

prognostic = <PrognosticClass>.load_model(
    <PrognosticClass>.load_default_package()
)
print(prognostic.input_coords())
print(prognostic.output_coords(prognostic.input_coords()))
```

Then construct a compatible source and backend and run:

```python
from earth2studio.data import <DataSourceClass>
from earth2studio.io import ZarrBackend
from earth2studio.run import deterministic

source = <DataSourceClass>()
io = ZarrBackend("forecast.zarr")
step = prognostic.output_coords(prognostic.input_coords())["lead_time"]
# Confirm that step is one positive model increment before deriving nsteps.
nsteps = 8
result = deterministic(
    ["2024-01-01T00:00:00"], nsteps, prognostic, source, io,
    device="cuda", verbose=True,
)
```

The placeholder class names are intentional: only use classes and targeted
extras verified for the chosen Earth2Studio version and domain. Compare the
source's variable vocabulary and grid with `input_coords()`. A data source may
need credentials, a local cache, or data-specific extras; those concerns are
not solved by `run.deterministic`.

For a derived field, load both model contracts before execution:

```python
from earth2studio.models.dx import <DiagnosticClass>
from earth2studio.run import diagnostic

diagnostic_model = <DiagnosticClass>.load_model(
    <DiagnosticClass>.load_default_package()
)
print(diagnostic_model.input_coords())
print(diagnostic_model.output_coords(diagnostic_model.input_coords()))
result = diagnostic(
    ["2024-01-01T00:00:00"], nsteps, prognostic, diagnostic_model,
    source, io, device="cuda", verbose=True,
)
```

If `diagnostic_model.input_coords()` asks for variables not emitted by the
prognostic, change the prognostic/source pairing or build a custom adapter. Do
not silently substitute variables with similar names.

## 4. Lead-time and output planning

For a model step `dt`, the horizon represented by `nsteps` is
`nsteps * dt`. The workflow's coordinate array includes zero through the final
step, so expect `nsteps + 1` lead-time positions per initialization time. For
multiple initialization times, expect one time slice per input time; verify the
backend's storage shape rather than assuming a particular array order.

A conservative planning sequence is:

1. Convert requested times with `to_time_array` or pass accepted time values
   directly to the run API.
2. Read the model output lead-time coordinate and confirm its unit/type.
3. Require an integer number of steps; round only after deciding the desired
   horizon, never as an implicit model change.
4. Use `output_coords` only for values on or safely mappable to produced
   coordinates.
5. Do one or two CPU mock steps before a long or remote run.
6. Record model package version, data source, time list, `nsteps`, device,
   output restriction, and checkpoint status with the output.

## 5. Configuration checker fixture

The bundled checker accepts a JSON description of these contracts without
importing Earth2Studio or accessing the network. `data_variables` is optional
but, when present, must cover every model input variable; `data_coords` is for
physical/domain dimensions. A useful mismatch case is:

```json
{
  "workflow": "deterministic",
  "time": ["2024-01-01T00:00:00"],
  "nsteps": 2,
  "data_variables": ["t2m", "u10m"],
  "data_coords": {
    "lat": [0, 1, 2, 3],
    "lon": [0, 1, 2, 3]
  },
  "model_input_coords": {
    "batch": [],
    "lead_time": [0],
    "variable": ["t2m", "u10m"],
    "lat": [0, 1, 2],
    "lon": [0, 1, 2, 3]
  },
  "model_output_coords": {
    "batch": [],
    "lead_time": [6],
    "variable": ["t2m", "u10m"],
    "lat": [0, 1, 2],
    "lon": [0, 1, 2, 3]
  },
  "output_coords": {
    "variable": ["t2m"],
    "lat": [0, 2]
  }
}
```

Run `python scripts/check_workflow_config.py --config workflow.json` from any
working directory. It should report a successful deterministic plan plus a
non-fatal mapping note for the extra source latitude. Add `--strict` when a
pipeline policy requires every data/model coordinate to match exactly. The
checker does not prove model weights, source availability, interpolation
quality, numerical correctness, or scientific validity.

