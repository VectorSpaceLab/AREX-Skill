---
name: serialization-and-advanced
description: "Persist GemPy GeoModel objects, validate and round-trip JSON or
  .gempy files, extract meshes, configure centered-grid gravity, and use
  optional topology, property, Subsurface, and legacy integrations safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: EUPL 1.2
---

# Serialization and advanced GemPy

Use this route after a `GeoModel` has been constructed and, where needed,
computed. It owns persistence, schema validation, mesh extraction, geophysics,
topology/property plugins, Subsurface conversion, and GemPy 2/3 compatibility.
It does **not** own initial model construction or ordinary grids/plots.

## Route and safety gate

- Build/map/compute the model in [modeling](../modeling/SKILL.md).
- Use [grids-and-visualization](../grids-and-visualization/SKILL.md) for dense,
  section, custom, topography, ordinary active-grid, and plotting setup.
- Use [environment-and-troubleshooting](../environment-and-troubleshooting/SKILL.md)
  for installation, backend selection, missing-package diagnosis, and version
  drift. This skill only classifies dependencies for its workflows.
- Use private temporary output paths. Never overwrite a valuable model before a
  successful load/validation check. Persistence functions create a missing
  parent directory for `.gempy` output, but JSON helpers do not promise that.
- Persistence is local and deterministic in principle; it does not download
  data. The source examples often use network data, plotting, or interactive
  windows, so use the self-contained patterns below instead.

## Fast decision table

| Need | Entry point | Result / gate |
|---|---|---|
| Native binary model archive | `gp.save_model(model, path, validate_serialization=True)` | `.gempy` ZIP archive; load and compare counts/structure |
| Native binary restore | `gp.load_model("model.gempy")` | `GeoModel`; requires exact `.gempy` suffix |
| Pydantic JSON snapshot | `model.model_dump_json(by_alias=True, indent=2)` | JSON text; restore with binary context, see reference |
| Tutorial JSON interchange | `JsonIO.save_model_to_json` / `load_model_from_json` | portable data/grid/series JSON; not the same as `.gempy` |
| Dense-grid mesh | `set_meshes_with_marching_cubes(model)` | vertices/faces on each element; needs dense computed output + `scikit-image` |
| Gravity forward setup | `gp.set_centered_grid` + `gp.calculate_gravity_gradient` | centered kernel and `GeophysicsInput`; compute owns final solution |
| Topology/property | external `gempy_plugins` modules | optional, version-matched plugin only |
| Subsurface mesh/data | `model.solutions...meshes_to_subsurface()` or `gp.compute_model(..., to_subsurface=True)` where supported | optional `subsurface`, usually PyVista for display |
| GemPy 3 to legacy | `gempy.API.gp2_gp3_compatibility.gp3_to_gp2_input.gempy3_to_gempy2` | requires `gempy_legacy`; compatibility surface is narrow |

## Persistence workflow

1. Keep the model object in memory and ensure its input data, structural group
   order, fault relation matrix, grid, and interpolation options are in the
   intended state. If it will be computed after restore, compute it after
   loading; solutions are runtime/cache state, not a replacement for source
   inputs.
2. Save a binary archive:

   ```python
   import gempy as gp
   archive = gp.save_model(model, "artifacts/model.gempy",
                           validate_serialization=True)
   restored = gp.load_model(archive)
   assert len(restored.surface_points_copy.xyz) == len(model.surface_points_copy.xyz)
   assert len(restored.orientations_copy.xyz) == len(model.orientations_copy.xyz)
   ```

   `save_model` defaults a missing path to `<model.meta.name>.gempy`; a path
   without a suffix gets `.gempy` appended. Any present non-`.gempy` suffix
   raises `ValueError`. `load_model` raises `ValueError` for a missing/wrong
   suffix and `FileNotFoundError` for a missing file. Both currently emit a
   development warning; do not treat that warning as a successful validation.
   The default validation compares input-table bytes and the model string.
3. Recompute explicitly with `gp.compute_model(restored)` when downstream
   solutions, meshes, or gravity are required. A `.gempy` archive stores a
   JSON header plus `input.bin` and `grid.bin`; do not hand-edit the archive.
4. For faulted models, compare group names/order and
   `np.array_equal(original.structural_frame.fault_relations,
   restored.structural_frame.fault_relations)`. The loader temporarily removes
   serialized fault names, validates the Pydantic model, then restores relations;
   this is why a fault round-trip must be tested rather than inferred from a
   surface-point count.

Detailed archive and Pydantic patterns are in
[references/persistence-reference.md](references/persistence-reference.md).

## JSON workflows and validation

### Pydantic model JSON

`GeoModel.model_dump_json(by_alias=True, indent=2)` serializes the Pydantic
model/header. `GeoModel.model_validate_json(text)` needs the binary payload
context for binary-backed input/grid fields. For a native binary round-trip,
prefer `gp.save_model`/`gp.load_model`; if inspecting the JSON header directly,
use the context manager with the original `input_tables_binary` and `grid_binary`:

```python
from gempy.core.data.encoders.converters import loading_model_from_binary
text = model.model_dump_json(by_alias=True, indent=2)
with loading_model_from_binary(model.structural_frame.input_tables_binary,
                               model.grid.grid_binary):
    restored = gp.data.GeoModel.model_validate_json(text)
restored.validate()
```

`GeoModel.validate()` is semantic validation, not a generic JSON-schema
validator. `gp.compute_model` calls it by default; `skip_validation=True` is an
explicit escape hatch only for a known, intentional diagnostic case. It raises
`ModelValidationError` for empty input, empty groups, underdetermined input, or
an out-of-order `BASEMENT` group. Pydantic errors can still arise from malformed
field types/enums. See `gempy/VALIDATION_SPEC.md` facts summarized in
[references/troubleshooting.md](references/troubleshooting.md).

### `gempy.modules.json_io.JsonIO`

This is a separate, file-oriented interchange format:

```python
from gempy.modules.json_io import JsonIO
JsonIO.save_model_to_json(model, "artifacts/model.json")
portable = JsonIO.load_model_from_json("artifacts/model.json")
portable.validate()
```

Required top-level JSON keys are `surface_points`, `orientations`, and
`grid_settings`. The validator mutates the loaded dictionary with defaults:
point/orientation `nugget`, IDs, orientation polarity, default metadata, and
series structural relation. Coordinates and gradients must be numeric; polarity
must be `1` or `-1`; grid resolution/extent and optional interpolation options
must have the expected container/types. Missing required keys or fields raise
`ValueError` with a field-specific message. A JSON load may synthesize a default
`Strat_Series` and default grid/interpolation settings. JSON save/load is not a
promise to preserve computed solution caches byte-for-byte.

For deterministic smoke testing without source data, run:

```bash
python scripts/json_roundtrip_smoke.py
```

The helper generates a tiny model, writes only temporary `.json`/`.gempy`
artifacts, checks both round-trips, and reports missing core prerequisites
instead of reading checkout files.

## Advanced capabilities

- **Mesh extraction:** Compute a dense-grid solution with mesh extraction
  enabled, then call `from gempy.modules.mesh_extranction.marching_cubes import
  set_meshes_with_marching_cubes`. It requires `model.solutions` to have
  `DENSE_GRID`, interpolation outputs, a dense regular grid, and `scikit-image`.
  It stores `vertices` and triangular `edges` on each structural element. A
  missing dense solution or output raises `ValueError`; a missing `skimage` is
  an environment failure. Do not use this as a plotting route; hand display to
  grids/visualization.
- **Centered-grid gravity:** Create measurement centers as an `N x 3` NumPy
  array, then call `gp.set_centered_grid(grid=model.grid, centers=centers,
  resolution=[nx, ny, nz], radius=scalar_or_3_vector)`. Compute
  `tz = gp.calculate_gravity_gradient(model.grid.centered_grid)` and set
  `model.geophysics_input = gp.data.GeophysicsInput(tz=tz,
  densities=np.asarray(densities))`. Set `mesh_extraction=False` when gravity
  is the only result needed, then compute with a compatible CPU NumPy config.
  The kernel is centered-grid geometry; densities must match the model's
  expected units/order. Gravity computation is numerical and can be expensive;
  validate shapes and one small center before scaling up.
- **Topology:** The tutorial API is external: `from gempy_plugins.topology_analysis
  import topology as tp`, after a computed model. `tp.compute_topology(model)`
  returns `(edges, centroids)`; adjacency and label helpers operate on those
  values. Missing `gempy_plugins` is not a GemPy core failure. Do not silently
  substitute an invented internal topology API.
- **Properties/kriging:** `gempy_plugins.property_estimation` uses GSTools and
  conditioning data to assign domains and run configured kriging/simulation.
  It is optional and can be expensive, stochastic, and visualization-heavy;
  keep seeds and domain decisions explicit. Missing GSTools/plugin is not a
  persistence error.
- **Subsurface:** Optional `subsurface` is required by
  `gp.set_topography_from_subsurface_structured_grid`,
  `gp.set_topography_from_file`, borehole conversion, and the
  `meshes_to_subsurface()` solution helpers. Mesh display through Subsurface
  normally also needs its PyVista stack. `require_subsurface()` raises a
  targeted `ImportError`; install/diagnose it through the environment route.
  Network-backed example datasets are not part of this workflow. Export arrays
  or unstructured data to a caller-owned path/object and check vertex/cell
  lengths before passing to a simulator.
- **Legacy compatibility:**
  `gempy3_to_gempy2(model)` is a narrow adapter that requires
  `gempy_legacy`; it creates a legacy model, transfers tabular inputs, extent,
  resolution, and structural mapping. The reverse output adapter consumes
  engine `Solutions` and a legacy `Project`. Treat this as migration glue, not
  a general `.gempy` loader, and verify the legacy package/API version first.

For signatures, shape checks, and integration snippets see
[references/advanced-integrations.md](references/advanced-integrations.md).

## Recovery checklist

1. Classify the failure: wrong suffix/file, malformed JSON/schema, Pydantic
   validation, semantic model validation, dense-grid/mesh precondition, numeric
   gravity, or optional import.
2. Preserve the failing artifact and inspect a copy. For JSON, parse with
   `json.load`, report the first missing/type-invalid field, then rerun
   `JsonIO._validate_json_schema` on a copy. For `.gempy`, do not unzip/edit;
   rerun save with validation and compare the original/loaded input bytes.
3. If a restored model fails compute, call `restored.validate()` and inspect
   group names, structural relations, fault matrix shape, grid active types,
   and interpolation options before using `skip_validation=True`.
4. If mesh extraction fails, verify dense solution type, output availability,
   regular-grid resolution, and `scikit-image`; if gravity fails, verify
   centered-grid centers/resolution/radius, `tz.shape`, densities length, and
   that the chosen backend supports the requested dtype/device.
5. If only topology, kriging, Subsurface, PyVista, or legacy import fails,
   report that optional boundary separately. Do not reinstall GemPy core or
   claim the model archive is corrupt without a core reproduction.

See [references/troubleshooting.md](references/troubleshooting.md) for the
failure matrix and links back to modeling and environment routes.
