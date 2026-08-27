# Advanced integrations reference

This reference keeps the advanced APIs concrete while keeping optional package
boundaries visible. Use a small computed model first; do not begin with the
large network-backed tutorial datasets.

## Dense-grid mesh extraction

The built-in extraction helper is in the `gempy.modules.mesh_extranction`
package:

```python
from gempy.modules.mesh_extranction import marching_cubes

# model must already have a computed dense solution
marching_cubes.set_meshes_with_marching_cubes(model)
for group in model.structural_frame.structural_groups:
    for element in group.elements:
        if element.vertices is not None:
            print(element.name, element.vertices.shape, element.edges.shape)
```

Observed preconditions:

- `model.solutions` is not `None`;
- `model.solutions.block_solution_type` is
  `RawArraysSolution.BlockSolutionType.DENSE_GRID`;
- interpolation outputs exist;
- the model has a dense `regular_grid` whose resolution/extent describe the
  scalar field reshape;
- `scikit-image` is importable (`skimage.measure.marching_cubes`).

`extract_mesh_for_element(structural_element, regular_grid, scalar_field,
mask=None)` is the lower-level function. It uses the element's
`scalar_field_at_interface`, reshapes with `regular_grid.resolution`, uses
`regular_grid.dx/dy/dz` as spacing, shifts vertices by the regular-grid lower
extent, and stores vertices/faces on the element. It accepts NumPy arrays and
converts Torch tensors to NumPy in the current implementation. A missing dense
solution or interpolation output produces `ValueError`; missing `skimage` is an
optional-dependency failure. Mesh extraction can be memory-intensive at high
resolution, so lower the grid before debugging.

This helper creates geometry data but does not display it. Route visualization
to the grids/visualization skill and treat PyVista/viewer as optional.

## Centered-grid gravity

The public signatures inspected in this package are:

```python
gp.set_centered_grid(
    grid: gempy.core.data.grid.Grid,
    centers: numpy.ndarray,
    resolution: Sequence[float],
    radius: float | Sequence[float],
) -> gempy_engine.core.data.centered_grid.CenteredGrid

gp.calculate_gravity_gradient(
    centered_grid: gempy_engine.core.data.centered_grid.CenteredGrid,
    ugal: bool = True,
) -> numpy.ndarray
```

A safe CPU setup is:

```python
import numpy as np
import gempy as gp

centers = np.asarray([[5.0, 5.0, 0.0]], dtype=float)
centered = gp.set_centered_grid(
    grid=model.grid,
    centers=centers,
    resolution=np.array([6, 6, 8]),
    radius=np.array([20.0, 20.0, 20.0]),
)
tz = gp.calculate_gravity_gradient(centered)
model.geophysics_input = gp.data.GeophysicsInput(
    tz=tz,
    densities=np.asarray([2.60, 2.75], dtype=float),
)
model.interpolation_options.mesh_extraction = False
solution = gp.compute_model(model)
print(solution.gravity)
```

The density vector must be ordered to the model's element/lithology convention;
its valid length is model-dependent. Inspect the structural frame and verify
`tz`/density shapes before compute. The centered grid becomes active through
`set_centered_grid`; if other active grids are retained, route active-grid
management to grids/visualization and intentionally reset it there. Gravity is
a forward computation and may be expensive for many centers or large kernels.
Use a deterministic one-center smoke before scaling up. Do not claim physical
units without checking the `ugal` choice, density units, and project convention.

## Fault relation models

For persistence tests, a synthetic fault model should preserve both structural
order and the relation matrix. A native model can be assembled by modeling
first, then:

```python
import numpy as np
import gempy as gp

# Names and surfaces must already exist in model.
gp.map_stack_to_surfaces(
    gempy_model=model,
    mapping_object={
        "Fault_Series": ["fault"],
        "Strat_Series": ["rock2", "rock1"],
    },
)
gp.set_is_fault(model, ["Fault_Series"])
gp.set_fault_relation(model, np.asarray([[0, 1], [0, 0]], dtype=int))
```

The exact relation matrix dimensions are the number of structural groups, not
necessarily the number of surfaces. Save/load and `JsonIO` tests must compare
the matrix after restore. If a model uses a special fault relation enum, compare
that enum on the loaded groups too. For a larger but still local regression,
create a two-fault matrix and test that group order is unchanged after both
formats.

## Topology plugin boundary

Topology in the supplied advanced tutorial is not a core GemPy module:

```python
from gempy_plugins.topology_analysis import topology as tp

edges, centroids = tp.compute_topology(model)
matrix = tp.get_adjacency_matrix(model, edges, centroids)
node_to_lith = tp.get_lot_node_to_lith_id(model, centroids)
node_to_fault = tp.get_lot_node_to_fault_block(model, centroids)
```

The model must already be computed, and topology uses the lithology/fault block
solution. Plotting helpers (`plot_adjacency_matrix`, `plot_topology`) are
optional viewer/display operations. `gempy_plugins` is separate from GemPy;
absence must be reported as `ModuleNotFoundError`/installation diagnosis, not as
an invalid model or failed `.gempy` round-trip.

## Property estimation boundary

Property estimation is also in `gempy_plugins`, with GSTools as a geostatistics
backend. The tutorial's public names include:

```python
from gempy_plugins.property_estimation.conditioning_data import ConditioningData
from gempy_plugins.property_estimation.domains import compute_domains
from gempy_plugins.property_estimation.kriging import KrigingDomainConfig, run_kriging
from gempy_plugins.property_estimation.simulation import SimulationDomainConfig, run_simulation
```

The normal order is: compute GemPy model -> `compute_domains(model)` -> assign
conditioning data domains -> make per-domain configs -> run kriging/simulation.
Domain keys can be tuples to merge geometrically split fault blocks. Keep random
seeds, variogram models, and configured domains in the experiment record. These
workflows are optional, potentially stochastic/expensive, and should not be
made a core skill prerequisite.

## Subsurface conversion/export

Core code gates Subsurface via `gempy.optional_dependencies.require_subsurface`
and raises:

```text
ImportError: The subsurface package is required to run this function.
```

Supported public-facing patterns evidenced by the package/tests include:

```python
# After compute, depending on the installed engine solution class:
mesh_data = model.solutions.raw_arrays.meshes_to_subsurface()
# or
mesh_data = model.solutions.meshes_to_unstruct()
```

The returned object is intended for Subsurface's unstructured-data structures.
A typical optional consumer constructs a `TriSurf` and converts it through
`subsurface.visualization.to_pyvista_mesh`; plotting additionally needs
PyVista/display support. Tests also show direct construction with
`subsurface.UnstructuredData.from_array(vertex=..., cells=..., vertex_attr=...,
cells_attr=...)`. Check that each face/cell index references the concatenated
vertex array and that attribute row counts match before export.

`gp.compute_model(..., to_subsurface=True)` appears in an integration example;
confirm the installed `compute_model`/engine version accepts that keyword before
using it because the current public signature exposes `**kwargs` but the core
engine's Subsurface path is optional. Network-backed NetCDF/well examples are
not safe smoke tests. For an existing Subsurface structured grid, the grid API
also provides `gp.set_topography_from_subsurface_structured_grid`; ordinary
file loading adds its own Subsurface reader requirement.

## Legacy compatibility

The adapter module is:

```python
from gempy.API.gp2_gp3_compatibility.gp3_to_gp2_input import gempy3_to_gempy2
legacy_model = gempy3_to_gempy2(model)
```

It calls `require_gempy_legacy()`, creates a legacy project, transfers surface
point/orientation dataframes, extent, resolution, and the structural mapper.
It is not a generic loader for old files. The output adapter
`set_gp3_solutions_to_gp2_solution(gp3_solution, geo_model)` consumes engine
solutions and a legacy `Project`, and transfers block/scalar/mesh arrays. Both
paths require a version-compatible `gempy_legacy` and should be tested in an
isolated optional environment. A missing legacy package must not be conflated
with Pydantic or `.gempy` corruption.

## Optional dependency matrix

| Capability | Core CPU | Extra boundary | Typical failure |
|---|---:|---|---|
| `.gempy`, Pydantic JSON, `JsonIO` | yes | none beyond GemPy Engine | suffix/schema/Pydantic error |
| centered gravity | yes | engine geophysics support | shape/backend/numeric error |
| marching cubes | mostly | `scikit-image` | missing import or dense-output `ValueError` |
| 2-D/3-D display | no | `gempy_viewer`, PyVista, display backend | import/headless/render failure |
| topology/property | no | `gempy_plugins`; GSTools for property | module/plugin API failure |
| Subsurface mesh/data | no | `subsurface`; PyVista for display | targeted optional import failure |
| legacy adapter | no | `gempy_legacy` | targeted optional import failure |
| Torch/autodiff GPU | no | `torch`, compatible CUDA/backend | backend/device/dtype failure |

Install and dependency decisions belong to
[environment-and-troubleshooting](../../environment-and-troubleshooting/SKILL.md).
