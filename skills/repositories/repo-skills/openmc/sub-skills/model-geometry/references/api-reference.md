# Model-construction API reference

This reference records the public Python behavior needed to construct OpenMC
inputs. Prefer the installed package's introspection for version-specific
additions, but preserve the validation and XML contracts below.

## IDs and ownership

Most model domains use `IDManagerMixin`: `Material`, `Surface`, `Cell`,
`Universe`, `RectLattice`, `HexLattice`, and plot objects allocate positive
IDs when their ID is omitted. `openmc.reset_auto_ids()` clears the auto-ID
counters for all ID-managed classes; use it only at a deliberate test/model
boundary. Passing an already-used explicit ID emits `openmc.IDWarning` rather
than silently changing ownership. Negative IDs are rejected for domains whose
minimum is positive. If IDs must coexist across objects, assign explicit,
non-overlapping IDs or keep references to the objects that own each ID.

Names are labels and are not identity. Use IDs or object references for fills,
regions, lattice entries, and source constraints.

`openmc.Nuclide(name)` is a string-like nuclide object whose `.name` is the
canonical value. Legacy names containing a hyphen, `Nat`, or a trailing `m` are
normalized with a warning; prefer GNDS-style names such as `U235`, `C0`, or
`Am242_m1` in new inputs.

## Materials and nuclides

`openmc.Material(material_id=None, name='', temperature=None, density=None,
density_units='sum', depletable=False, volume=None, components=None,
percent_type='ao')` creates a material. Build its composition with:

```python
mat.add_nuclide('H1', 2.0, percent_type='ao')
mat.add_element('O', 1.0)
mat.set_density('g/cm3', 1.0)
```

`Material.add_nuclide(nuclide, percent, percent_type='ao')` accepts a string,
a real nonnegative amount, and `ao` or `wo`. `Material.add_element` expands a
natural element and can accept enrichment arguments; use the element name,
not an element-ID spelling, for ordinary composition. `set_density` accepts
`g/cm3`, `g/cc`, `kg/m3`, `atom/b-cm`, `atom/cm3`, `sum`, and `macro`. A
non-`sum` density requires a numeric value. `add_s_alpha_beta(name)` adds
thermal scattering metadata; it is a data-library concern, not a replacement
for nuclide composition.

Material temperature is in kelvin and is a default for cells using that
material. `Cell.temperature` takes precedence over material temperature, and a
cell's density similarly overrides its material density. A material's
`nuclides` list contains `(name, percent, percent_type)` records. XML export of
a `Materials` collection writes `materials.xml`; no transport or cross-section
file is needed merely to serialize the Python collection.

## Surfaces, regions, and cells

Use algebraic surface classes such as `XPlane`, `YPlane`, `ZPlane`, `Plane`,
`XSphere`/`YSphere`/`ZSphere`, `Sphere`, and `ZCylinder`. Surface constructors
accept an optional `surface_id`, `boundary_type`, `albedo`, and `name` in
addition to their geometry-specific parameters. Boundary types are
`transmission`, `vacuum`, `reflective`, `periodic`, and `white`; albedo must be
positive and is meaningful for reflective, periodic, and white boundaries.
Periodic surfaces can be paired through `surface.periodic_surface`; the
periodicity is constrained by the supported axis-aligned/planar rules.

Unary `-surface` and `+surface` produce negative and positive half-spaces.
Combine regions with `&` (intersection), `|` (union), and `~` (complement):

```python
inside = -openmc.ZCylinder(r=0.4)
shell = +openmc.ZCylinder(r=0.4) & -openmc.ZCylinder(r=0.5)
```

`openmc.Region.from_expression(expression, surfaces)` can reconstruct a region
from signed surface IDs. A half-space or Boolean region can be assigned to
`Cell(region=...)`; an omitted region is unbounded. `Cell(fill=...)` accepts a
`Material`, `UniverseBase`, `Lattice`, `None` (void), or an iterable of
materials for distributed materials. An invalid fill type or non-Region region
raises a validation exception rather than being deferred to XML.

A cell can carry `temperature`, `density`, `volume`, `translation`, and
`rotation`. Temperatures and densities must be positive when present and may be
iterables for distributed instances. A cell filled by a universe or lattice
propagates assigned temperature/density to contained material cells. A
translation is a length-three vector. Rotation accepts three angles or a 3x3
matrix; inspect `cell.rotation_matrix` when checking the applied transform.

`cell.bounding_box` delegates to its region and returns an
`openmc.BoundingBox`; void/no-region cells are infinite. Bounding boxes can
contain `numpy.inf` for unbounded axes, and exotic/non-axis-aligned surfaces
may not yield a tight finite box.

## Universes, lattices, and geometry

`openmc.Universe(cells=...)` groups cells and can be used as a repeated cell
fill. `Universe.add_cell`, `add_cells`, `remove_cell`, `find(point)`, and
`bounding_box` are useful for construction checks. `openmc.Geometry(root)`
accepts a root universe or an iterable of cells (the latter creates a root
universe). Its useful inspection methods include `find(point)`,
`get_all_cells()`, `get_all_materials()`, `get_all_universes()`,
`get_all_lattices()`, `get_all_surfaces()`, `determine_paths()`, and
`get_instances(paths)`.

A `RectLattice` needs `lower_left`, `pitch`, `universes`, and usually `outer`.
Its assigned universe array is ordered as z/y/x (or y/x in 2-D), while natural
indices and `get_universe` use Cartesian x/y(/z) coordinates. Check `shape`,
`indices`, `is_valid_index`, `get_universe`, and `find_element` instead of
assuming NumPy row order is physical y order. A `HexLattice` needs `center`,
`pitch`, `universes`, and usually `outer`; its universes are ragged lists from
outermost ring to innermost, with ring entries ordered from the top clockwise.
The valid `orientation` values are `x` and `y`; `indices` exposes `(r, i)` or
`(z, r, i)` coordinates, but assigned list positions are not those natural
coordinates. Use `get_universe` and `show_indices()` when preparing a hex
layout.

`Geometry.bounding_box` delegates to the root universe. `Geometry.export_to_xml(path='geometry.xml', remove_surfs=False)` writes a
`<geometry>` document; passing a directory appends `geometry.xml`. Set
`geometry.merge_surfaces = True` when redundant surface removal is wanted;
treat the deprecated `remove_surfs` argument as compatibility only. A geometry
can be loaded with `Geometry.from_xml(path, materials=...)`, where materials
may be a `Materials` object or a path to `materials.xml`.

## Sources and settings

`openmc.IndependentSource` accepts `space`, `angle`, `energy`, `time`,
`strength`, `particle`, and optional `constraints`. Common distributions are
`openmc.stats.Point`, `Box`, `PointCloud`, `Isotropic`, `Discrete`, `Uniform`,
`Tabular`, and `PolarAzimuthal`. The four distribution properties are type
checked. Constraints can restrict `domains` (cells/materials/universes),
`time_bounds`, `energy_bounds`, `fissionable`, and a rejection strategy.
`CompiledSource`, `FileSource`, and `MeshSource` are separate source types;
compiled/file sources need external artifacts and should not be used by an
XML-only fixture unless those paths are intentional.

`Settings()` defaults to eigenvalue mode. For a minimal valid simulation input,
set `batches`, `particles`, and a source; set `inactive` for an eigenvalue
source-convergence phase when appropriate. `run_mode` accepts `eigenvalue`,
`fixed source`, `volume`, `plot`, and `particle restart`. `Settings.source`
accepts one `SourceBase` or a mutable sequence of them. Setters validate types,
positive counts, and enumerated values. Settings XML round-trips source
subelements and configured options; export does not execute the model.

## Model, plots, and XML

`openmc.Model(geometry=None, materials=None, settings=None, tallies=None,
plots=None, description='')` owns the complete input graph. The installed
signature is `Model(geometry=None, materials=None, settings=None, tallies=None,
plots=None, description='')`. `model.bounding_box` delegates to geometry.
`model.export_to_xml(directory='.')` writes separate settings, geometry,
materials, optional tallies, and optional plots files. It can derive materials
from geometry when the explicit collection is empty. `model.export_to_model_xml(path='model.xml')` writes one `<model>` document. Both methods
serialize only; `Model.run` is outside this route.

`openmc.SlicePlot` is the most useful geometry-debugging plot. Set `basis`,
`origin`, `width`, `pixels`, and optionally `color_by`; put it in
`openmc.Plots([...])` and call `export_to_xml()`. `SlicePlot.from_geometry` is
convenient only when the selected geometry bounding box has finite coordinates
for the selected plane. `VoxelPlot`, `RayTracePlot`, and
`WireframeRayTracePlot` have additional native/runtime implications. Plot XML
is an input description; producing image/voxel output is a separate operation.
