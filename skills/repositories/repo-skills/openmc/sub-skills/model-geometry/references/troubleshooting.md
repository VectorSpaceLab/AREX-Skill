# Model and geometry troubleshooting

## Validation and ownership

- **`TypeError` from a setter:** check the concrete object type and scalar/
  iterable shape first. Material composition amounts are real numbers;
  `Cell.region` must be a `Region`; `Cell.fill` must be a material, universe,
  lattice, `None`, or a material iterable; lattice entries must be universes.
  Do not cast an invalid object merely to bypass the check.
- **`ValueError` from a setter:** inspect enumerated values and positivity/
  length constraints. Common examples are invalid density units, negative
  temperature/density/pitch, a non-three-component translation, an unsupported
  lattice orientation, or a source distribution of the wrong family.
- **`IDWarning`:** two objects claimed the same explicit ID. Decide which
  object owns the ID, use distinct explicit IDs, or call
  `openmc.reset_auto_ids()` before constructing a fresh isolated graph. Never
  hide the warning and assume XML references will be repaired.
- **Objects appear to have stale IDs in a test:** auto-ID counters are process
  state. Reset at the test boundary, not halfway through a graph that already
  has references. Rebuild the graph after resetting if necessary.

## Materials and fills

- **Density is `None` or ignored:** `sum` is the default density unit and does
  not store a numeric density. Supply `set_density('g/cm3', value)` (or another
  supported unit) when a physical density is required. A density value passed
  with `sum` is warned as ignored.
- **Material composition is unexpectedly expanded:** `add_element` expands
  natural isotopes and enrichment into nuclide records. Inspect `nuclides`
  after composition. Use `add_nuclide` when exact isotope names are required.
- **Adding a nuclide fails after a macroscopic/NCrystal definition:** those
  material modes are mutually exclusive with ordinary nuclide additions. Make
  the material choice explicit; data-library setup is outside this route.
- **`Cell.fill` rejects a list:** distributed material fills are iterables of
  `Material` (or `None` entries where supported), not arbitrary nested geometry
  objects. A universe or lattice is assigned as one object.
- **Temperature/density seems not to apply:** precedence is cell over material,
  and a cell filled by a universe/lattice propagates values into contained
  material cells. Check the target cell's `fill_type` and read the contained
  cell values after assignment.

## CSG, boundaries, and bounds

- **A shell has the wrong material:** verify half-space signs. For a surface
  equation, `-surface` is the negative side and `+surface` is the positive side;
  a shell usually uses `+inner & -outer`. Check membership at representative
  points with `point in region` or `geometry.find(point)`.
- **Overlaps or leaks are suspected:** XML serialization does not prove that
  cells partition space. Construct mutually exclusive Boolean regions, add a
  bounding outer cell, and inspect points at the center, shell, and boundary.
  Native geometry-debug/transport checks belong to `setup-runtime`.
- **Bounding box contains infinities:** an infinite cylinder/plane or a cell
  without a region is unbounded; this is expected. Non-axis-aligned planes,
  cones, and composite surfaces may only provide a conservative or partially
  infinite box. Do not feed infinite bounds to a source or plot that requires a
  finite box; provide explicit source/plot bounds.
- **Periodic boundary setup is rejected:** periodicity is supported for paired
  planar surfaces under axis/normal-direction rules. Set
  `periodic_surface` explicitly for nontrivial pairs and check inward normals.
  Do not use periodicity as a generic substitute for a reflecting or vacuum
  boundary.

## Lattice indexing and transforms

- **Rectangular lattice lookup is mirrored:** assigned NumPy storage is z/y/x;
  natural lookup is Cartesian x/y(/z), and the y direction has a reversed
  physical relationship in the stored array. Use `indices`, `shape`,
  `get_universe`, and `find_element` on a tiny labeled-universe fixture rather
  than guessing from a diagram.
- **Hex lattice raises a ring-size error:** universes must be ragged,
  outermost-to-innermost, with six-sided ring counts and exactly one center
  universe. For 3-D, every axial slice must have the same ring structure.
- **Hex lattice gives unexpected positions:** list indices are not natural
  `(r, i)` coordinates. Check `orientation`, call `show_indices()`, and test
  `get_universe` for selected coordinates. Round-trip the XML before using a
  large assembly.
- **Transformed universe is not visible:** `Cell.translation` and `rotation`
  apply to a universe/lattice fill. Ensure the cell's region encloses the
  transformed content and inspect `rotation_matrix`; changing the child
  surfaces instead may be the intended model.
- **Distributed paths are unavailable:** call `geometry.determine_paths()`
  before reading `paths` or `num_instances`. A lattice/replicated universe can
  produce multiple instances, so a scalar temperature/density and an instance
  sequence have different meanings.

## Sources, settings, and XML

- **Source setter rejects a distribution:** `space` must be a `Spatial`, `angle`
  a `UnitSphere`, and `energy`/`time` a `Univariate`. `PointCloud` positions
  must be 3-D and strengths must match the number of points. Validate source
  XML with `IndependentSource.from_xml_element` when a round trip matters.
- **A source is accepted but later cannot be used:** a source domain constraint
  must reference a cell/material/universe in the model; compiled/file/mesh
  sources also require their external artifacts. XML-only checks can validate
  structure but cannot validate native loading or source sampling.
- **Settings values are missing from XML:** many settings are optional and
  omitted until explicitly assigned. Set the required run mode, batches,
  particles, and source for the intended input, then parse the generated XML.
  Do not confuse a valid settings document with a runnable transport setup.
- **`Model.export_to_xml` emits no materials:** an empty explicit `Materials`
  collection allows the model to derive materials from geometry; verify that
  each material fill is reachable. If deterministic membership matters, pass an
  explicit `openmc.Materials([...])` collection.
- **`Geometry.from_xml` cannot assign fills:** provide a matching
  `openmc.Materials` object or the correct `materials.xml` path. The geometry
  document contains IDs, while material objects resolve those IDs.
- **Parser succeeds but runtime fails:** stop at the boundary. Separate XML
  construction checks from native executable/shared-library checks and from
  cross-section/data checks. `openmc.lib` is optional native library mode and
  is not a base Python import requirement.
