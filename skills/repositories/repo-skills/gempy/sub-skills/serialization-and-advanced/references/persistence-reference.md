# Persistence and JSON reference

## Two formats, two contracts

GemPy exposes two intentionally different persistence paths:

| Format | API | Contents | Best use |
|---|---|---|---|
| `.gempy` | `gempy.save_model`, `gempy.load_model` | JSON-like model header plus binary input/grid chunks in a ZIP archive | Native model checkpoint and faithful input/grid round-trip |
| JSON interchange | `gempy.modules.json_io.JsonIO` | Explicit metadata, points, orientations, series, grid, interpolation options, fault matrix, and ID map | Human-readable interchange and migration fixtures |
| Pydantic JSON | `GeoModel.model_dump_json` / `model_validate_json` | Pydantic representation; binary-backed fields require context | Inspection, snapshots, and internal validation |

Do not call a JSON interchange file a `.gempy` archive. Do not use a model
header alone as a complete native restore unless the binary context is supplied.

## `.gempy` archive contract

Public calls and observed behavior:

```python
import gempy as gp

path = gp.save_model(
    model,
    path="out/checkpoint",       # becomes out/checkpoint.gempy
    validate_serialization=True, # default
)
restored = gp.load_model(path)
```

`save_model` accepts `GeoModel`, `path: str | None = None`, and
`validate_serialization: bool = True`. With `path=None`, it uses the model name
plus `.gempy`. If a path has no suffix, `.gempy` is appended. A present suffix
must be `.gempy` case-insensitively or `ValueError` is raised. Missing parent
directories are created. `load_model` requires an existing path whose suffix is
`.gempy`; otherwise it raises `ValueError` or `FileNotFoundError`.

The current implementation emits a development warning from both public calls.
The archive writer packs fixed entries named `header.json`, `input.bin`, and
`grid.bin` using ZIP deflate. The header is generated with
`model.model_dump_json(by_alias=True, indent=4)` inside a fault-relation
serialization context. The loader reads all three entries, validates the header
with `GeoModel.model_validate` inside `loading_model_from_binary(...)`, and
restores pending fault relation names. Keep this implementation detail as a
compatibility fact, not permission to edit internal entries.

With `validate_serialization=True`, saving serializes then reloads in memory and
compares surface-point and orientation table bytes plus normalized model string.
An assertion failure means the checkpoint should not be trusted. For a stronger
application-level gate, compare group names/order, relation enum values, fault
matrix, grid resolution/extent, and the number of input rows after loading.
Then compute the loaded model separately if results are needed.

Example fault-aware check:

```python
import numpy as np
import gempy as gp

before_groups = [g.name for g in model.structural_frame.structural_groups]
before_faults = np.asarray(model.structural_frame.fault_relations).copy()
path = gp.save_model(model, "out/fault-model.gempy")
copy = gp.load_model(path)
assert [g.name for g in copy.structural_frame.structural_groups] == before_groups
np.testing.assert_array_equal(copy.structural_frame.fault_relations, before_faults)
np.testing.assert_array_equal(
    copy.surface_points_copy.data, model.surface_points_copy.data
)
np.testing.assert_array_equal(
    copy.orientations_copy.data, model.orientations_copy.data
)
```

A saved computed model may have cache/solution behavior that differs after
loading. The supported recovery pattern is: restore inputs, re-check structure,
then call `gp.compute_model(copy)`.

## Pydantic JSON with binary context

The `GeoModel` Pydantic model has arbitrary types and NumPy encoders. A direct
header dump is useful for inspection:

```python
header = model.model_dump_json(by_alias=True, indent=2)
```

For `model_validate_json`, provide the original binary payloads through the
publicly importable context manager used by the package:

```python
from gempy.core.data.encoders.converters import loading_model_from_binary

with loading_model_from_binary(
    input_binary=model.structural_frame.input_tables_binary,
    grid_binary=model.grid.grid_binary,
):
    copy = gp.data.GeoModel.model_validate_json(header)
copy.validate()
```

This is a Pydantic restoration/inspection technique, not a replacement for the
`.gempy` file format. `model.model_dump_json` arguments are Pydantic v2
arguments; `by_alias=True` is the compatible choice used by GemPy's serializer.
Pydantic field/type failures are distinct from `GeoModel.validate()` semantic
failures.

## `JsonIO` interchange schema

Import the class from the package module:

```python
from gempy.modules.json_io import JsonIO
```

`JsonIO.save_model_to_json(model, file_path)` writes a JSON object with:

- `metadata`: name, creation date, last-modification date, owner;
- `surface_points`: objects with `x`, `y`, `z`, `id`, and `nugget`;
- `orientations`: objects with `x`, `y`, `z`, `G_x`, `G_y`, `G_z`, `id`,
  `nugget`, and `polarity`;
- `series`: group name, surface names, structural relation, and colors;
- `grid_settings`: regular-grid resolution, extent, and optional octree level;
- `interpolation_options`: kernel range/coefficient, mesh extraction, and
  octree-level settings;
- optional `fault_relations` and `id_name_mapping.name_to_id`.

`JsonIO.load_model_from_json(path)` loads the file, calls its internal schema
validator, creates point/orientation tables and a `Grid`, builds a structural
frame, maps series to surfaces, restores a square fault-relation matrix when
its shape matches the structural-group count, and applies colors when present.
It may synthesize a default `Strat_Series` when `series` is absent.

`JsonIO._validate_json_schema(data)` is a practical validator that raises
`ValueError`; it is not a Pydantic `ValidationError` and its return annotation is
incorrectly documented as `None` even though successful validation returns
`True` in the current implementation. It mutates `data` to add defaults. The
validator requires the top-level keys `surface_points`, `orientations`, and
`grid_settings`. Each point requires x/y/z; each orientation requires x/y/z and
G_x/G_y/G_z; grid settings require `regular_grid_resolution` and
`regular_grid_extent`. It validates optional colors as `#...` strings and
interpolation option types. The lower-level `_load_surface_points` and
`_load_orientations` methods then enforce numeric fields, integer IDs, and
orientation polarity in `{-1, 1}`.

Useful malformed-input probes:

```python
import copy
from gempy.modules.json_io import JsonIO

bad = {"surface_points": [], "orientations": []}
try:
    JsonIO._validate_json_schema(copy.deepcopy(bad))
except ValueError as exc:
    print(type(exc).__name__, str(exc))  # missing grid_settings

bad_orientation = [{"x": 0, "y": 0, "z": 0, "G_x": 0,
                    "G_y": 0, "G_z": 1, "id": 0,
                    "nugget": 0.01, "polarity": 2}]
try:
    JsonIO._load_orientations(bad_orientation)
except ValueError as exc:
    print(type(exc).__name__, str(exc))  # invalid polarity
```

Never use `eval` on JSON values, and write to a new file during repair. Dates and
metadata defaults can vary by run; compare semantics rather than raw JSON text.
