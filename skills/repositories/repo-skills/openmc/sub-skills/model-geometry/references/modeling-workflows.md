# Modeling workflows

The workflows below are construction recipes. Their output is Python objects
and XML input files, not a transport result. Keep every output in a caller-
selected directory so the recipe is independent of the current working
 directory.

## 1. Novice pin cell

**Inputs:** fuel composition, gap/cladding/moderator compositions, radii,
cell pitch, and a desired boundary condition. **Outputs:** a `Model`, separate
XML files, and optionally `model.xml`.

1. Create each `Material`, add nuclides/elements, and call `set_density` with
   explicit units. If using a natural element or enrichment, inspect the
   resulting `material.nuclides` before export.
2. Define concentric `ZCylinder` surfaces. Use negative half-spaces for the
   interiors and Boolean intersections for the gap/cladding shells.
3. Define the outer square using `openmc.model.RectangularPrism(width, height,
   boundary_type=...)`. Construct fuel, gap, cladding, and moderator cells so
   the regions cover the intended space without accidental overlap.
4. Build `Geometry([fuel, gap, clad, moderator])`. Check the bounding box and
   `geometry.find((0, 0, 0))` before exporting.
5. Set `Settings.batches`, `Settings.particles`, and an
   `IndependentSource(space=stats.Box(...), constraints={'fissionable': True})`
   for an eigenvalue input, or choose `run_mode='fixed source'` and a source
   appropriate to that calculation. These settings do not run anything.
6. Add a `SlicePlot` with a finite x/y width if a plot input is useful.
7. Export with `model.export_to_xml(directory=output_dir)` and, when a single
   document is required, `model.export_to_model_xml(output_dir/'model.xml')`.
   Parse every emitted XML file and assert the expected root tags.

A minimal XML-only fixture may use ordinary H/O/Fe-like compositions and a
small particle/batch count; these numbers are input metadata, not a scientific
recommendation. No `OPENMC_CROSS_SECTIONS` setting is needed for this workflow's
Python construction and XML checks.

## 2. Reusable universes and rectangular lattice

**Inputs:** one or more pin-universe builders, a 2-D/3-D universe array,
`lower_left`, `pitch`, and an outer universe. **Outputs:** a lattice-filled
cell and a root geometry.

1. Build a pin universe with material-filled cells and a moderator/outer cell.
   Keep the universe references; do not rebuild equivalent objects for every
   lattice position unless per-instance state is required.
2. Create `RectLattice`, assign `lower_left` and positive `pitch`, then assign
   `universes`. In a 2-D array, the first nested dimension is the physical y
   layout represented by the package's z/y/x storage convention; check
   `lattice.shape`, `lattice.indices`, and `lattice.get_universe((x, y))`.
3. Set `lattice.outer` when points outside the array must map to a universe.
   Fill an enclosing cell with the lattice and bound it with a box or other
   region. A lattice with missing required properties fails when serialized.
4. For a 3-D array, use z/y/x nested storage and a three-component pitch and
   lower-left. Check `find_element` at representative points, including a
   point outside the lattice that should reach the outer universe.
5. Call `geometry.get_all_*` methods to confirm nested objects are reachable,
   then export and inspect `<lattice>`, `<universes>`, `<lower_left>`, and
   `<pitch>` XML elements.

For material or temperature fields repeated across a lattice, call
`geometry.determine_paths()` before reading `paths` or `num_instances`; those
properties intentionally raise until paths are determined.

## 3. Hexagonal lattice and transformations

**Inputs:** concentric ring lists, center, radial/axial pitch, orientation, and
an optional axial stack. **Outputs:** a `HexLattice` and an XML-round-trippable
geometry.

1. Build ragged `universes` from outermost ring to innermost ring. A ring with
   `n` rings has `6*(n-1-r)` entries for an outer ring `r`, except the center
   ring, which has one entry. In 3-D, repeat the same ring structure per axial
   slice.
2. Assign `center`, one radial pitch for 2-D or radial plus axial pitch for
   3-D, and `orientation='x'` or `'y'`. Set `outer` to handle positions outside
   the finite lattice.
3. Check `num_rings`, `num_axial`, `indices`, and `get_universe` for the
   intended natural coordinates. Do not infer natural `(r, i)` positions from
   the nested-list indices. Switch orientation only deliberately and repeat
   representative lookups.
4. Put the lattice in a bounded cell and check `geometry.bounding_box`. Export,
   load with `Geometry.from_xml(..., materials=...)`, and compare lattice
   center, pitch, orientation, ring counts, and selected universe IDs.
5. For a transformed repeated universe, assign `cell.translation` or
   `cell.rotation` only to a cell filled with a universe/lattice. Inspect
   `rotation_matrix`, the emitted cell attributes, and `geometry.find` at a
   point whose containing cell is known. A transformation does not replace a
   correct enclosing region.

## 4. Independent and custom sources

**Inputs:** spatial/angle/energy/time distributions, particle type, strength,
and optional domain constraints. **Outputs:** `Settings` with source XML.

1. Start with `IndependentSource`. For a point source use `stats.Point`; for a
   bounded source use `stats.Box(lower_left, upper_right)`; use `stats.PointCloud`
   for explicit points and strengths.
2. Add `stats.Isotropic()` or another `UnitSphere` distribution when the
   default isotropic behavior is not sufficient. Use `stats.Discrete` for a
   monoenergetic or finite line spectrum and `stats.Uniform`/`Tabular` for
   energy or time ranges. Energies are in eV and time is in seconds.
3. Use `particle='photon'` (or another supported particle identifier) only when
   the intended model enables the corresponding physics later. Use
   `constraints={'domains': [cell_or_material_or_universe]}` to reject spatial
   samples outside named domains; check the domain objects are part of the
   geometry.
4. For multiple independent sources, pass a mutable sequence to
   `settings.source`, set relative `strength` values, and consider
   `uniform_source_sampling` when deliberately converting strength to weight.
5. Serialize `source.to_xml_element()` or `settings.export_to_xml()` and parse
   the source type/strength and child distributions. This validates the input
   description without sampling or running it.
6. `CompiledSource` and `FileSource` preserve external library/file paths in
   XML. Use them only when the caller supplies and owns those artifacts;
   neither is appropriate for the self-contained default fixture.

## 5. Validation and XML round trip

Use this order for a reliable construction check:

- **Python graph:** assert `isinstance` for root geometry, fills, regions,
  lattice entries, sources, and settings; inspect IDs and names.
- **Topology:** call `geometry.find` at points in each intended region and
  `geometry.get_all_cells/materials/universes/lattices/surfaces`.
- **Bounds:** compare finite coordinates with `numpy.testing` and explicitly
  allow `numpy.inf` where the model is unbounded.
- **XML:** parse with `lxml.etree`; assert roots (`geometry`, `materials`,
  `settings`, `plots`, or `model`) and required IDs/child tags.
- **Round trip:** use `Materials.from_xml`, `Geometry.from_xml`, and
  `Settings.from_xml` on separate files. For combined input, use the model XML
  loader only as an input-structure check; do not call `run` or `init_lib`.

An XML parse success proves serialization, not that a native executable can
transport particles. Keep cross-section and build checks in `setup-runtime`.
